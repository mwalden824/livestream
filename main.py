from flask import Flask, render_template, request, session, redirect, url_for, send_file
from flask_socketio import join_room, leave_room, send, SocketIO
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import random
from string import ascii_letters
from werkzeug.security import generate_password_hash, check_password_hash
from os import path
import hashlib

DB_NAME = "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysupersecretkeybitch"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
db = SQLAlchemy(app)
# db.init_app(app)

# class User(db.Model, UserMixin):
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    streamKey = db.Column(db.String(20), unique=True, nullable=False)

if not path.exists(DB_NAME):
    with app.app_context():
        db.create_all()
        # db.create_all(app=app)
        print("Database created")

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

socketio = SocketIO(app)

# NOTE:  Should probably use redis database if app gets big
rooms = {}

@app.route("/", methods=["POST", "GET"])
def home():
    return render_template("home.html")

@app.route("/<streamer>", methods=["POST", "GET"])
def streamname(streamer):
    user = User.query.filter_by(username=streamer).first()
    if user:
        if str(streamer) not in rooms:
            session["room"] = str(streamer)
            rooms[str(streamer)] = {"members": 0, "messages": []}

        return render_template("streamer.html", msgs=rooms[streamer]["messages"], username=streamer, stream_key=streamer)
    else:
        return render_template("no-account.html", username=streamer)

@app.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username-login')
        password = request.form.get('password-login')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                print("Logged in Successfully")
                login_user(user, remember=True)
                session["name"] = str(user.username)
                return redirect(request.referrer)
            else:
                # flash('')
                print("Incorrect Password")
        else:
            print("Username doesn't exist")
            # flash('')

    return 'Authentication Error'

@app.route("/signup", methods=['POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username-signup')
        email = request.form.get('email-signup')
        password = request.form.get('password-signup')
        password2 = request.form.get('password2-signup')

    user = User.query.filter_by(email=email).first()
    if user:
        # flash('Email already exists.')
        print('Email already exists')
    elif len(email) < 4:
        # flash('')
        print('Email too short')
    elif len(username) < 4:
        # flash('')
        print('Username too short')
    elif password != password2:
        # flash('')
        print("Passwords don't match")
    elif len(password) < 8:
        # flash('')
        print('password too short')
    else:
        # Calculate a hash from the username and password with sha256 and 
        # keep first 20 characters to use for stream key
        stream_key = hashlib.sha256((username + password).encode()).hexdigest()[0:19]
        new_user = User(username=username, email=email, password=generate_password_hash(password, method='sha256'), streamKey=stream_key)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        print('Account created')
        return redirect(request.referrer)
    
    return 'Error in Account Creation', 404

@app.route("/logout")
def logout():
    logout_user()
    return redirect(request.referrer)

@app.route('/stream/<streamer>/index.m3u8')
def serve_playlist(streamer):
    user = User.query.filter_by(username=streamer).first()
    streamKey = user.streamKey
    try:
        return send_file('stream/'+streamKey+'/index.m3u8', mimetype='application/x-mpegURL')
    except:
        return "Playlist not found", 404

@app.route('/stream/<streamer>/<int:segment_number>.ts')
def serve_segment(streamer, segment_number):
    user = User.query.filter_by(username=streamer).first()
    streamKey = user.streamKey
    segment_path = f'stream/{streamKey}/{segment_number}.ts'
    return send_file(segment_path, mimetype='video/MP2T')

@app.route('/stream-auth', methods=['POST'])
def auth_stream():
    if request.method == 'POST':
        stream_key = request.form.get('name')
        user = User.query.filter_by(streamKey=stream_key).first()
        if user:
            return "Stream Allowed", 200
        else:
            return "Stream Denied", 406
    else:
        return "Error", 404


@socketio.on("message")
def message(data):
    room = session.get("room")
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    name = session.get("name")
    room = session.get("room")
    if not name:
        return
    
    if room not in rooms:
        return

    join_room(room)
    rooms[str(room)]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    name = session.get("name")
    room = session.get("room")
    leave_room(room)

    if room not in rooms:
        return

    rooms[str(room)]["members"] -= 1
    print(f"{name} has left the room {room}")


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5001)

