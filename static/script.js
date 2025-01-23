const socket = io();

const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

// 发送消息
function sendMessage() {
    const msg = messageInput.value;
    if (msg.trim() !== '') {
        socket.send(msg); // 发送消息到服务器
        messageInput.value = ''; // 清空输入框
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
    messageElement.textContent = msg;
    messagesDiv.appendChild(messageElement);

    // 滚动到底部
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});
