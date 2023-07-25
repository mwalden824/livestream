var chatOpen = true;
const chatButton = document.getElementById('open-chat-button');
const offlineChatButton = document.getElementById('open-chat-button-offline');

function show() {
    document.getElementById('sidebar').classList.toggle('active');
    document.getElementById('main').classList.toggle('active');
    document.getElementById('content').classList.toggle('active');
}

function showChat() {
    if (chatOpen == true) {
        chatOpen = false;
        if (isPlaying) {
            chatButton.style.display = 'block';
        }
        else {
            offlineChatButton.style.display = 'block';
        }
    } else {
        chatOpen = true;
        if (isPlaying) {
            chatButton.style.display = 'none';
        }
        else {
            offlineChatButton.style.display = 'none';
        }
    }

    document.getElementById('left-sidebar').classList.toggle('active');
    document.getElementById('main').classList.toggle('left-active');
}


var socketio = io();

const messages = document.getElementById('chatMessages');

const createMessage = (name, msg) => {
    const msgContent = `
    <div class="row">
        <span class="screenname">${name}:</span>
        <span class="message">${msg}</span>
    </div>
    `;
    messages.innerHTML += msgContent;
};

socketio.on("message", (data) => {
    console.log("A message has been transmitted");
    createMessage(data.name, data.message);
});

const sendMessage = () => {
    const userMessage = document.getElementById('chatTextBox');
    if (userMessage.value == "") return;
    socketio.emit("message", { data: userMessage.value });
    userMessage.value = "";
};

const msgTextBox = document.getElementById('chatTextBox');
msgTextBox.addEventListener("keydown", function (e) {
    if (e.code == "Enter") {
        sendMessage();
    }
});

