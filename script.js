function show() {
    document.getElementById('sidebar').classList.toggle('active');
    document.getElementById('main').classList.toggle('active');
    document.getElementById('content').classList.toggle('active');
}

function showChat() {
    document.getElementById('left-sidebar').classList.toggle('active');
    document.getElementById('main').classList.toggle('left-active');
}
