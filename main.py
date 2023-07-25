from flask import Flask, render_template, request, session, redirect, url_for, send_file
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_letters

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysupersecretkeybitch"
socketio = SocketIO(app)

# Set this to streamer's username when you setup account, auth, etc.
# rooms = {}
room = "UKnowWho"
members = 0

messages = []

def generate_random_username():
    letters = ascii_letters
    return ''.join(random.choice(letters) for _ in range(5))

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    session["name"] = generate_random_username()
    if session.get("name") is None:
        # Handle case where user hasn't set their name
        return    

    print("The messages are: ")
    print(messages)
    return render_template("index.html", msgs=messages)

@app.route('/stream/hls/stream.m3u8')
def serve_playlist():
    return send_file('stream/hls/stream.m3u8', mimetype='application/x-mpegURL')

@app.route('/stream/hls/stream-<int:segment_number>.ts')
def serve_segment(segment_number):
    segment_path = f'stream/hls/stream-{segment_number}.ts'
    return send_file(segment_path, mimetype='video/MP2T')

@socketio.on("message")
def message(data):
    # room = session.get("room")
    global messages
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room)
    # send(content)
    messages.append(content)
    print(f"{session.get('name')} said: {data['data']}")
    print(messages)

@socketio.on("connect")
def connect(auth):
    global members
    name = session.get("name")
    if not name:
        return

    join_room(room)
    members = members + 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    global members
    name = session.get("name")
    leave_room(room)

    members = members - 1

    print(f"{name} has left the room {room}")


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)

