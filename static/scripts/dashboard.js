// Retrieved from: https://www.freecodecamp.org/news/check-if-a-javascript-string-is-a-url/
// Function to validate the structure of URLs
const isValidUrl = urlString=> {
    var urlPattern = new RegExp('^(https?:\\/\\/)?'+ // validate protocol
  '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // validate domain name
  '((\\d{1,3}\\.){3}\\d{1,3}))'+ // validate OR ip (v4) address
  '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // validate port and path
  '(\\?[;&a-z\\d%_.~+=-]*)?'+ // validate query string
  '(\\#[-a-z\\d_]*)?$','i'); // validate fragment locator
return !!urlPattern.test(urlString);
}

function closeDashboardAlert() {
    document.getElementById('dashboard-alert').style.display = 'none';
}

function openDashboardAlert(alertMsg) {
    var dashboardAlertElement =  document.getElementById('dashboard-alert');
    var dashboardAlertMsgElement =  document.getElementById('dashboard-alert-msg');
    dashboardAlertMsgElement.innerHTML = alertMsg;
    dashboardAlertElement.style.display = 'block';
}

$(document).ready(function() {
    $("#dashboard-save-button").click(function () {
        var oldPassword = $("#old-password-textbox").val();
        var newPassword = $("#new-password-textbox").val();
        var newPasswordRetry = $("#new-password-retry-textbox").val();

        // If user is attempting to change password, do checks on input
        if (oldPassword.length != 0) {
            // Make sure newpassword and Retry password match
            if (newPassword != newPasswordRetry) {
                openDashboardAlert("Retry password doesn't match");
                return;
            }

            // Make sure the character count of password is within the limit
            if (newPassword.length < 8 || newPassword.length > 20) {
                openDashboardAlert("New Password needs to be between 8 and 20 characters");
                return;
            }

            // Make sure the user isn't changing to same password
            if (newPassword == oldPassword) {
                openDashboardAlert("New password should be different from old one");
                return;
            }
        }

        var smYoutube = $("#sm-youtube").val();
        var smTwitter = $("#sm-twitter").val();
        var smInstagram = $("#sm-instagram").val();
        var smDiscord = $("#sm-discord").val();
        var smTiktok = $("#sm-tiktok").val();

        // Make sure social media links are valid urls
        if (!isValidUrl(smYoutube) && smYoutube.length != 0) {
            openDashboardAlert("Invalid YouTube URL");
            return;
        }

        if (!isValidUrl(smTwitter) && smTwitter.length != 0) {
            openDashboardAlert("Invalid Twitter URL");
            return;
        }

        if (!isValidUrl(smInstagram) && smInstagram.length != 0) {
            openDashboardAlert("Invalid Instagram URL");
            return;
        }

        if (!isValidUrl(smDiscord) && smDiscord.length != 0) {
            openDashboardAlert("Invalid Discord URL");
            return;
        }

        if (!isValidUrl(smTiktok) && smTiktok.length != 0) {
            openDashboardAlert("Invalid Tik-Tok URL");
            return;
        }

        var description = $("#dashboard-description-textbox-id").val();

        // Check that length of description isn't too long
        if (description.length > 500) {
            openDashboardAlert("Description should be 500 characters or less");
            return;
        }

        var data = {
            "old_password": oldPassword,
            "new_password": newPassword,
            "new_password_retry": newPasswordRetry,
            "sm_youtube": smYoutube,
            "sm_twitter": smTwitter,
            "sm_instagram": smInstagram,
            "sm_discord": smDiscord,
            "sm_tiktok": smTiktok,
            "description": description
        };

        $.ajax({
            type: "POST",
            url: "/save_settings",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function(response) {
                openDashboardAlert('Settings saved successfully!');
            },
            error: function(error) {
                openDashboardAlert(error.responseJSON.message);
            }
        });
    });
});


