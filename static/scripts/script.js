var chatOpen = true;
const chatButton = document.getElementById('open-chat-button');
const offlineChatButton = document.getElementById('open-chat-button-offline');

var imageFallback = document.getElementById('offline-image-placeholder');
var videoElement = document.getElementById('videoElement');
var videoPlayerElement = document.getElementById('videoPlayer');
var openChatBtn = document.getElementById('open-chat-btn');
var openChatBtnOffline = document.getElementById('open-chat-button-offline');

var isPlaying = true;

openChatBtnOffline.style.display = 'none';
videoPlayerElement.addEventListener("error", function() {
    console.log("Video Error");
    videoElement.style.display = 'none';
    imageFallback.style.display = 'block';
    isPlaying = false;
});
var videoPlayer = videojs('videoPlayer', {
    autoplay: 'muted',
    muted: true
});
videoPlayer.src({
    // src: '../stream/hls/stream.m3u8',
    src: '/stream/hls/stream.m3u8',
    // src: '/home/mwalden/Projects/livestream/stream/hls/stream.m3u8',
    type: 'application/x-mpegURL'
});
videoPlayer.on('error', function (event) {
    console.log('Video Error');
    videoElement.style.display = 'none';
    imageFallback.style.display = 'block';
    isPlaying = false;
});
videoPlayer.play();
videoPlayer.muted(false);        

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
// messages.scrollTop = messages.scrollHeight;

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
    messages.scrollTop = messages.scrollHeight;
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

function showSignupPopup() {
    document.getElementById('signupPopup').style.display = 'block';
}

function closeSignupPopup() {
    document.getElementById('signupPopup').style.display = 'none';
}

function showLoginPopup() {
    document.getElementById('loginPopup').style.display = 'block';
}

function closeLoginPopup() {
    document.getElementById('loginPopup').style.display = 'none';
}

// Add a click event listener to the signup button
document.getElementById('signup-button').addEventListener('click', showSignupPopup);

// Add a click event listener to the login button
document.getElementById('login-button').addEventListener('click', showLoginPopup);
