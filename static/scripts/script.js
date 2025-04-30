
function show() {
    var sbar = document.getElementById('sidebar');
    var main = document.getElementById('main');
    var content = document.getElementById('content');
    var dashb = document.getElementById('dashboard');

    if (sbar) {
        sbar.classList.toggle('active');
    }
    if (main) {
        main.classList.toggle('active');
    }
    if (content) {        
        content.classList.toggle('active');
    }
    if (dashb) {        
        dashb.classList.toggle('active');
    }
}

function showSignupPopup() {
    document.getElementById('signupPopup').style.display = 'block';
}

function closeSignupPopup() {
    document.getElementById('signupPopup').style.display = 'none';
}

function showLoginPopup() {
    console.log("A message has been transmitted");
    document.getElementById('loginPopup').style.display = 'block';
}

function closeLoginPopup() {
    document.getElementById('loginPopup').style.display = 'none';
}


var signupButton = document.getElementById('signup-button');
// Add a click event listener to the signup button
if (signupButton) {
    signupButton.addEventListener('click', showSignupPopup);
}

var loginButton = document.getElementById('login-button');
// Add a click event listener to the login button
if (loginButton) {
    loginButton.addEventListener('click', showLoginPopup);    
}

var streamersDiv = document.getElementById('streamers-id');

function updateOnlineStreamers() {
    $.ajax({
        url: '/streamers_update',
        type: 'POST',
        data: {
            // Your POST data here
        },
        success: function(response) {
            // console.log('POST request successful:', response);
            // Using a for loop
            var streamersHTML = '';
            for (let i = 0; i < response.online.length; i++) {
                const username = response.online[i];
                // console.log(username);
                streamersHTML += `
                <a href="/${username}">
                    <div class="streamer-row">
                        <div class="streamer-pic"><img src="/storage/${username}/profile-pic.jpg" id="icon"></div>
                        <div class="streamer-name">${username}</div>
                    </div>
                </a>
            `;
            }
            if (response.offline) {
                for (let i = 0; i < response.offline.length; i++) {
                    const username = response.offline[i];
                    // console.log(username);
                    streamersHTML += `
                    <a href="/${username}">
                        <div class="streamer-row">
                            <div class="streamer-pic"><img src="/storage/${username}/profile-pic-offline.jpg" id="icon"></div>
                            <div class="streamer-name">${username}</div>
                        </div>
                    </a>
                `;
                }
            }
            streamersDiv.innerHTML = streamersHTML;
          },
        error: function(xhr, status, error) {
            console.error('POST request failed:', error);
        }
    });
}

// Initial Update request when the page loads
updateOnlineStreamers();

// Repeating the Update request every 30 seconds
setInterval(updateOnlineStreamers, 30000); // 30000 milliseconds = 30 seconds

function closeLoginErrorAlert() {
    document.getElementById('login-error-alert').style.display = 'none';
}

function showLoginErrorAlert(alertMsg) {
    var errorAlertElement =  document.getElementById('login-error-alert');
    var errorAlertMsgElement =  document.getElementById('login-error-alert-msg');
    errorAlertMsgElement.innerHTML = alertMsg;
    errorAlertElement.style.display = 'block';
}

function closeSignupErrorAlert() {
    document.getElementById('signup-error-alert').style.display = 'none';
}

function showSignupErrorAlert(alertMsg) {
    var errorAlertElement =  document.getElementById('signup-error-alert');
    var errorAlertMsgElement =  document.getElementById('signup-error-alert-msg');
    errorAlertMsgElement.innerHTML = alertMsg;
    errorAlertElement.style.display = 'block';
}

$(document).ready(function() {
    $("#submit-signup").click(function () {
        var username = $("#username-signup-id").val();
        var email = $("#email-signup-id").val();
        var password = $("#password-signup-id").val();
        var password2 = $("#password2-signup-id").val();

        var data = {
            "username-signup": username,
            "email-signup": email,
            "password-signup": password,
            "password2-signup": password2
        };

        $.ajax({
            type: "POST",
            url: "/signup",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function(response) {
                // openDashboardAlert('Settings saved successfully!');
                location.reload();
            },
            error: function(error) {
                showSignupErrorAlert(String(error.responseJSON.message));
                setTimeout(closeSignupErrorAlert, 5000);
            }
        });
    });
});

$(document).ready(function() {
    $("#submit-login").click(function () {
        var username = $("#username-login-id").val();
        var password = $("#password-login-id").val();

        console.log(username)
        console.log(password)

        var data = {
            "username-login": username,
            "password-login": password
        };

        $.ajax({
            type: "POST",
            url: "/login",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function(response) {
                // openDashboardAlert('Settings saved successfully!');
                location.reload();
            },
            error: function(error) {
                showLoginErrorAlert(String(error.responseJSON.message));
                setTimeout(closeLoginErrorAlert, 5000);
            }
        });
    });
});
