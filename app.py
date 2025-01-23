from flask import Flask, render_template
from flask_socketio import SocketIO, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# 渲染主页
@app.route('/')
def index():
    return render_template('index.html')

# 处理消息
@socketio.on('message')
def handle_message(msg):
    print(f"Message received: {msg}")
    send(msg, broadcast=True)  # 向所有用户广播消息

if __name__ == '__main__':
    
    socketio.run(app, host='::', port=80, debug=True)
