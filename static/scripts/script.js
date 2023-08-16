
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

// Add a click event listener to the signup button
document.getElementById('signup-button').addEventListener('click', showSignupPopup);

// Add a click event listener to the login button
document.getElementById('login-button').addEventListener('click', showLoginPopup);
