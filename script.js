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
