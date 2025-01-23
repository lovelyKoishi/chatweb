const socket = io();

const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

// 发送消息
sendButton.addEventListener('click', () => {
    const msg = messageInput.value;
    if (msg.trim() !== '') {
        socket.send(msg); // 发送消息到服务器
        messageInput.value = '';
    }
});

// 接收消息
socket.on('message', (msg) => {
    const messageElement = document.createElement('div');
    messageElement.textContent = msg;
    messagesDiv.appendChild(messageElement);

    // 滚动到底部
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});
