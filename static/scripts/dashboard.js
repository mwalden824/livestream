var imageFallback = document.getElementById('offline-image-placeholder');
var videoElement = document.getElementById('videoElement');
var videoPlayerElement = document.getElementById('videoPlayer');

var isPlaying = true;

function closeDashboardAlert() {
    document.getElementById('dashboard-alert').style.display = 'none';
}

function openDashboardAlert(alertMsg) {
    var dashboardAlertElement =  document.getElementById('dashboard-alert');
    var dashboardAlertMsgElement =  document.getElementById('dashboard-alert-msg');
    dashboardAlertMsgElement.innerHTML = alertMsg;
    dashboardAlertElement.style.display = 'block';
}

videoPlayerElement.addEventListener("error", function() {
    // console.log("Video Error");
    videoElement.style.display = 'none';
    imageFallback.style.display = 'block';
    isPlaying = false;
});
var videoPlayer = videojs('videoPlayer', {
    autoplay: 'muted',
    muted: true
});
videoPlayer.src({
    src: '/stream/' + streamPath + '/index.m3u8',
    type: 'application/x-mpegURL'
});
videoPlayer.on('error', function (event) {
    // console.log('Video Error');
    videoElement.style.display = 'none';
    imageFallback.style.display = 'block';
    isPlaying = false;
});
videoPlayer.play();
videoPlayer.muted(false);        

function displayTags(inputString) {
    var tags = inputString.split(" ");

    var tagsHtml = document.getElementById('tags-of-stream');
    tagsHtml.innerHTML = "";

    if (inputString != "") {
        for (var i = 0; i < tags.length; i++) {
            tagsHtml.innerHTML += `
            <a href='/search/` + String(tags[i]) + `'>
                <div class='db-tag'>` + String(tags[i]) + `</div>
            </a>
            `;
        }
    }
}

$(document).ready(function() {
    $("#dashboard-save-button").click(function () {
        var title = $("#stream-title").val();
        var tags = $("#stream-tags").val();
        var category = $("#category-menu").val();

        var data = {
            "sTitle": String(title),
            "sTags": String(tags),
            "sCategory": String(category)
        };

        $.ajax({
            type: "POST",
            url: "/save_stream_settings",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function(response) {
                openDashboardAlert('Settings saved successfully!');
                displayTags(String(tags));
            },
            error: function(error) {
                openDashboardAlert(error.responseJSON.message);
            }
        });
    });
});

var chatMembersDiv = document.getElementById('chatMembers');

function chatAddMember(uname) {
    const chatMember = `
        <div class="chat-member-row">
            <span class="screenname">${uname}</span>
        </div>
    `;

    chatMembersDiv.innerHTML += chatMember;
}

function chatRemoveMember(uname) {
    const children = chatMembersDiv.children;
    for (let i = 0; i < children.length; i++) {
        const child = children[i];
        for (let j = 0; j < child.children.length; j++) {
            const innerChild = child.children[j];
            // console.log(innerChild.innerHTML)
            if (innerChild.innerHTML === uname) {
                // Delete span and div parent objects
                // console.log(child.parentElement);
                chatMembersDiv.removeChild(innerChild.parentElement);
                console.log("Parent and child removed!");
                return;
            }
        }
    }

    console.log("No matching username");
}

var socketio = io();

const messages = document.getElementById('db-chatMessages');
// const viewerCount = document.getElementById('viewers-number-id');
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
    // console.log("A message has been transmitted");
    if (data.type === "chat") {
        createMessage(data.name, data.message);
        messages.scrollTop = messages.scrollHeight;    
    }
    else if (data.type === "count") { 
        // viewerCount.innerHTML = data.message;
        if (data.action === "add") {
            chatAddMember(data.name);
        }
        else if (data.action === "remove") {
            chatRemoveMember(data.name);
        }
    }
});

const sendMessage = () => {
    const userMessage = document.getElementById('db-chatTextBox');
    if (userMessage.value == "") return;
    socketio.emit("message", { data: userMessage.value });
    userMessage.value = "";
};

const msgTextBox = document.getElementById('db-chatTextBox');
msgTextBox.addEventListener("keydown", function (e) {
    if (e.code == "Enter") {
        sendMessage();
    }
});

function setCategoryValue(ctg) {
    var selectElement = document.getElementById("category-menu");
    selectElement.value = ctg;
}

setCategoryValue(streamCategory);

