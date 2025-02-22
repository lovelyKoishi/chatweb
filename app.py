import os
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'EGIN EC PRIVATE KEdsgdfshshersghshfsdhgafh'
socketio = SocketIO(app, async_mode='gevent')


# 强制 HTTPS 访问钩子（排除 /httpwarning 路由，避免重定向循环）
@app.before_request
def enforce_https():
    if request.path.startswith('/httpwarning'):
        return  # 排除 /httpwarning 路由
    if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
        return redirect(url_for('http_warning'))


# HTTP访问警告路由，重定向到 https://hajimitv.top
@app.route('/httpwarning')
def http_warning():
    print("redirect success")
    return redirect("https://hajimitv.top")


users = []
message_history = []  # 维护消息历史记录

def load_message_history():
    if os.path.exists('message_history.txt'):
        with open('message_history.txt', 'r', encoding='utf-8') as file:
            for line in file:
                message_history.append(line.strip())

def save_message_to_file(msg):
    with open('message_history.txt', 'a', encoding='utf-8') as file:
        file.write(msg + '\n')

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
    message_history.append(msg)  # 添加到历史记录
    save_message_to_file(msg)      # 保存消息到文件
    send(msg, broadcast=True)      # 向所有用户广播消息

# 处理用户加入
@socketio.on('join')
def handle_join(username):
    print(f"User {username} joined")
    join_room(username)
    for msg in message_history:
        emit('message', msg)

if __name__ == '__main__':
    delete_message_history_file()  # 删除历史消息文件
    load_message_history()           # 加载历史消息

    from gevent.pywsgi import WSGIServer
    from geventwebsocket.handler import WebSocketHandler
    import gevent

    ssl_args = {
        'certfile': '_.hajimitv.top.pem',
        'keyfile': '_.hajimitv.top.key',
        'server_side': True
    }
    http_server = WSGIServer(('', 80), app, handler_class=WebSocketHandler)
    https_server = WSGIServer(('', 443), app, handler_class=WebSocketHandler, **ssl_args)

    gevent.spawn(http_server.serve_forever)
    https_server.serve_forever()
