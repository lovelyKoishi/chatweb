const socket = io();

const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const setUsernameButton = document.getElementById('set-username-button');
const usernameInput = document.getElementById('username-input');


// 发送消息
function sendMessage() {
    const msg = messageInput.value;
    if (msg.trim() !== '') {
        const fullMessage = `${username}: ${msg}`;  // 将用户名和消息结合
        socket.send(fullMessage);  // 发送带用户名的消息
        messageInput.value = '';  // 清空输入框
    }
}

// 点击发送按钮时发送消息
sendButton.addEventListener('click', sendMessage);

// 按下 Enter 键时也发送消息
messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {  // 检测是否按下 Enter 键
        event.preventDefault();  // 防止换行
        sendMessage();
    }
});

// 接收消息
socket.on('message', (msg) => {
    const messageElement = document.createElement('div');
    messageElement.textContent = msg;  // 显示带用户名的消息
    messagesDiv.appendChild(messageElement);

    // 滚动到底部
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});

