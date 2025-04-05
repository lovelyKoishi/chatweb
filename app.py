import os
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, 
                   async_mode='gevent',
                   ping_timeout=5,  # 超时时间缩短为 5 秒
                   ping_interval=2)  # 心跳间隔缩短为 2 秒

# 全局变量
message_history = []  # 消息历史记录
online_users = set()  # 在线用户集合
user_rooms = defaultdict(set)  # 用户与房间的映射
user_last_active = {}  # 用户最后活跃时间

def load_message_history():
    if os.path.exists('message_history.txt'):
        with open('message_history.txt', 'r', encoding='utf-8') as file:
            for line in file:
                try:
                    username, message, timestamp = line.strip().split('|')
                    message_history.append({
                        'username': username,
                        'message': message,
                        'timestamp': int(timestamp)  # 转换为整数
                    })
                except ValueError:
                    # 忽略格式错误的行
                    continue

def save_message_to_file(msg):
    with open('message_history.txt', 'a', encoding='utf-8') as file:
        file.write(f"{msg['username']}|{msg['message']}|{msg['timestamp']}\n")

def delete_message_history_file():
    if os.path.exists('message_history.txt'):
        os.remove('message_history.txt')

def cleanup_inactive_users():
    """清理不活跃用户"""
    current_time = time.time()
    inactive_users = []
    
    for user, last_active in user_last_active.items():
        if current_time - last_active > 10:  # 10秒不活跃视为离线
            inactive_users.append(user)
    
    for user in inactive_users:
        handle_user_leave(user)
        print(f"Cleaned up inactive user: {user}")

# 路由
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    key = request.form['key']
    if key == 'miku':  # 替换为你的密钥
        session['logged_in'] = True
        return redirect(url_for('chat'))
    else:
        return '密钥错误', 401

@app.route('/chat')
def chat():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/online_users')
def get_online_users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return jsonify({'users': list(online_users)})

@app.route('/leave', methods=['POST'])
def handle_leave_request():
    data = request.get_json()
    username = data.get('username')
    if username and username in online_users:
        handle_user_leave(username)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'user not found'}), 404

def handle_user_leave(username):
    """处理用户离开的逻辑"""
    if username in online_users:
        online_users.discard(username)
        rooms = user_rooms.pop(username, set())
        for room, sid in rooms:  # 解包房间和 sid
            leave_room(room, sid=sid, namespace='/')  # 显式传递 namespace
            emit('system_message', {'message': f'{username} 离开了聊天室'}, room=room, namespace='/')
        user_last_active.pop(username, None)
        emit('user_list_update', {'users': list(online_users)}, broadcast=True, namespace='/')
        print(f"User {username} left the chat")

# Socket.IO事件处理
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    # 找出断开连接的用户
    username = None
    for user in list(online_users):
        if request.sid in user_rooms[user]:
            username = user
            break
    
    if username:
        handle_user_leave(username)  # 立即处理用户离开

@socketio.on('join')
def handle_join(data):
    username = data.get('username')
    room = data.get('room', 'main')
    
    if username:
        print(f"User {username} joined room {room}")
        online_users.add(username)
        user_rooms[username].add((room, request.sid))  # 存储房间和 sid
        user_last_active[username] = time.time()
        join_room(room)
        
        # 发送欢迎消息和历史消息
        emit('system_message', {'message': f'欢迎 {username} 加入聊天室!'}, room=room, namespace='/')
        emit('user_list_update', {'users': list(online_users)}, broadcast=True, namespace='/')
        
        # 发送最近50条历史消息
        for msg in message_history[-50:]:
            emit('message', msg, room=request.sid, namespace='/')  # 只发送给当前用户

@socketio.on('message')
def handle_message(data):
    username = data.get('username')
    msg = data.get('message')
    timestamp = data.get('timestamp')  # 获取前端传递的发送时间
    
    if username and msg and timestamp:
        print(f"Message from {username}: {msg}")
        user_last_active[username] = time.time()
        formatted_msg = {
            'username': username,
            'message': msg,
            'timestamp': timestamp  # 使用前端传递的时间
        }
        message_history.append(formatted_msg)
        save_message_to_file(formatted_msg)  # 保存到文件
        emit('message', formatted_msg, broadcast=True)

@socketio.on('heartbeat')
def handle_heartbeat(data):
    username = data.get('username')
    if username and username in online_users:
        user_last_active[username] = time.time()

@socketio.on('change_username')
def handle_change_username(data):
    old_username = data.get('old_username')
    new_username = data.get('new_username')
    
    if old_username and new_username and old_username in online_users:
        # 从在线用户列表中移除旧用户名
        online_users.discard(old_username)
        
        # 更新用户房间映射
        user_rooms[new_username] = user_rooms.pop(old_username, set())
        
        # 更新用户最后活跃时间
        user_last_active[new_username] = user_last_active.pop(old_username, time.time())
        
        # 添加新用户名到在线用户列表
        online_users.add(new_username)
        
        # 广播用户列表更新
        emit('user_list_update', {'users': list(online_users)}, broadcast=True)
        
        print(f"User {old_username} changed username to {new_username}")
    else:
        emit('error', {'message': '用户名更改失败，可能是旧用户名不存在或新用户名无效'})

if __name__ == '__main__':
    load_message_history()  # 加载历史消息
    # 启动清理不活跃用户的定时任务
    def background_cleanup():
        with app.app_context():  # 推入 Flask 应用上下文
            while True:
                socketio.sleep(5)  # 每5秒检查一次
                cleanup_inactive_users()
    
    socketio.start_background_task(background_cleanup)
    
    print("Starting server...http://127.0.0.1:11451")
    socketio.run(app, host='0.0.0.0', port=11451, debug=True)