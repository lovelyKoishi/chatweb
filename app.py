import os
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'EGIN EC PRIVATE KEdsgdfshshersghshfsdhgafh'
socketio = SocketIO(app, async_mode='gevent')

users = []

# 维护消息历史记录
message_history = []

# 加载历史消息
def load_message_history():
    if os.path.exists('message_history.txt'):
        with open('message_history.txt', 'r', encoding='utf-8') as file:
            for line in file:
                message_history.append(line.strip())

# 保存消息到文件
def save_message_to_file(msg):
    with open('message_history.txt', 'a', encoding='utf-8') as file:
        file.write(msg + '\n')

# 删除历史消息文件
def delete_message_history_file():
    if os.path.exists('message_history.txt'):
        os.remove('message_history.txt')

# 渲染登录页
@app.route('/')
def login():
    return render_template('login.html')

# 处理登录
@app.route('/login', methods=['POST'])
def handle_login():
    key = request.form['key']
    if key == 'miku':  # 替换为你的密钥
        session['logged_in'] = True
        return redirect(url_for('index'))
    else:
        return '密钥错误', 401

# 渲染主页
@app.route('/chat')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

# 处理消息
@socketio.on('message')
def handle_message(msg):
    print(f"Message received: {msg}")
    message_history.append(msg)  # 将消息添加到历史记录
    save_message_to_file(msg)  # 保存消息到文件
    send(msg, broadcast=True)  # 向所有用户广播消息

# 处理用户加入
@socketio.on('join')
def handle_join(username):
    print(f"User {username} joined")
    join_room(username)
    # 发送历史消息给新加入的用户
    for msg in message_history:
        emit('message', msg)


if __name__ == '__main__':
    delete_message_history_file()  # 删除历史消息文件
    load_message_history()  # 加载历史消息
    ssl_context = ('_.hajimitv.top.pem', '_.hajimitv.top.key')
    socketio.run(app, host='::', port=443, debug=True, 
                certfile='_.hajimitv.top.pem',
                keyfile='_.hajimitv.top.key',
                server_side=True)
