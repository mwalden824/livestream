from flask import Flask, render_template, request, session, redirect, url_for, send_file, jsonify
from flask_socketio import join_room, leave_room, send, SocketIO
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import random
from string import ascii_letters
from werkzeug.security import generate_password_hash, check_password_hash
from os import path, mkdir, listdir
import hashlib
import socket
from PIL import Image
import subprocess
import shutil
import time
import threading

DB_NAME = "database.db"
# STREAM_HOST_NAME = socket.gethostbyname(socket.gethostname())
# STREAM_HOST_NAME = socket.gethostbyname(socket.getfqdn())
HOST_NAME = "10.0.0.80"
STREAM_PORT = 1935
STREAM_APP_NAME = "live"
STREAM_SERVER_URL = HOST_NAME + ":" + str(STREAM_PORT)
APP_PORT = 5001
STORAGE_PATH = "storage"
STREAM_PATH = "stream/"
THUMBNAIL_CREATION_PERIOD = 15 # seconds

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysupersecretkeybitch"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
db = SQLAlchemy(app)
# db.init_app(app)

default_descriptioin = "Streamer's description goes here."
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    streamKey = db.Column(db.String(20), unique=True, nullable=False)
    youtubeUrl = db.Column(db.String(40), default="")
    twitterUrl = db.Column(db.String(40), default="")
    instagramUrl = db.Column(db.String(40), default="")
    discordUrl = db.Column(db.String(40), default="")
    tiktokUrl = db.Column(db.String(40), default="")
    description = db.Column(db.String(500), default=default_descriptioin)

# if not path.exists(DB_NAME):
if not path.exists("instance/"+DB_NAME):
    with app.app_context():
        db.create_all()
        # db.create_all(app=app)
        print("Database created")

# Create storage folder where all user data will be stored
if not path.exists(STORAGE_PATH):
    mkdir(STORAGE_PATH)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

socketio = SocketIO(app)

# NOTE:  Should probably use redis database if app gets big
rooms = {}

def valid_extension(filename):
    _, extension = path.splitext(filename)
    valid_extensions = ['.png', '.jpg', '.jpeg']
    
    if extension.lower() in valid_extensions:
        return True
    else:
        return False

def create_latest_thumbnails():
    while True:
        for folder_name in listdir(STREAM_PATH):
            folder_path = path.join(STREAM_PATH, folder_name)

            if path.isdir(folder_path):
                # Call ffmpeg and create thumbnail for this stream
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',
                    '-i', folder_path+'/index.m3u8',
                    '-s', '480x270',
                    '-vframes', '1',
                    '-f', 'image2',
                    folder_path+'/thumbnail.jpg',
                    '-hide_banner',
                    '-loglevel', 'panic'
                ]

                try:
                    subprocess.run(ffmpeg_cmd, check=True)
                except subprocess.CalledProcessError as e:
                    print("Error executing FFmpeg command:", e)

                    try:
                        shutil.rmtree(folder_path)
                    except OSError as e:
                        print(f"Error deleting '{path}': {e}")

        # print("Thumbnail thread running")
        time.sleep(THUMBNAIL_CREATION_PERIOD)

@app.route("/", methods=["POST", "GET"])
def home():
    online_streamers = []
    for folder_name in listdir(STREAM_PATH):
        folder_path = path.join(STREAM_PATH, folder_name)
        tn_path = path.join(folder_path, "thumbnail.jpg")
        if path.isdir(folder_path) and path.exists(tn_path):
            user = User.query.filter_by(streamKey=folder_name).first()
            username = user.username
            online_streamers.append(username)

    return render_template("home.html", streamers_online=online_streamers)

@app.route("/<streamer>", methods=["POST", "GET"])
def streamname(streamer):
    user = User.query.filter_by(username=streamer).first()
    if user:
        session["room"] = str(streamer)
        if str(streamer) not in rooms:
            # session["room"] = str(streamer)
            rooms[str(streamer)] = {"members": 0, "messages": []}

        return render_template(
            "streamer.html", 
            msgs=rooms[streamer]["messages"], 
            username=streamer, 
            userDescription=user.description,
            smLinks=[user.youtubeUrl, user.twitterUrl, user.instagramUrl, user.discordUrl, user.tiktokUrl])
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
        mkdir(STORAGE_PATH + "/" + username)
        stream_key = hashlib.sha256((username + password).encode()).hexdigest()[0:19]
        new_user = User(username=username, email=email, password=generate_password_hash(password, method='sha256'), streamKey=stream_key)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        print('Account created')
        return redirect(request.referrer)
    
    return 'Error in Account Creation', 404

@app.route("/<streamer>/dashboard")
@login_required
def dashboard(streamer):
    user = User.query.filter_by(username=streamer).first()
    if user:
        if user.username == current_user.username:
            return render_template(
                "dashboard.html", 
                username=streamer, 
                ip_adress=STREAM_SERVER_URL, 
                app_name=STREAM_APP_NAME, 
                key_for_stream=user.streamKey, 
                youtube=user.youtubeUrl, 
                twitter=user.twitterUrl, 
                instagram=user.instagramUrl, 
                discord=user.discordUrl, 
                tiktok=user.tiktokUrl,
                userDescription=user.description)
        else:
            return render_template("access-denied.html", attempted_username=user.username, actual_username=current_user.username)
    else:
        return render_template("no-account.html", username=streamer)

@app.route("/save_settings", methods=['POST'])
@login_required
def save_settings():
    data = request.json

    user = User.query.filter_by(username=current_user.username).first()
    if len(data["old_password"]) > 0 and user:
        if check_password_hash(user.password, data["old_password"]):
            # Change password for current user
            user.password = generate_password_hash(data["new_password"], method='sha256')
            # db.session.commit()
        else:
            return jsonify({"message": "Incorrect password"}), 404

    # Save social media links
    user.youtubeUrl = data["sm_youtube"]
    user.twitterUrl = data["sm_twitter"]
    user.instagramUrl = data["sm_instagram"]
    user.discordUrl = data["sm_discord"]
    user.tiktokUrl = data["sm_tiktok"]

    # Save description
    user.description = data["description"]

    db.session.commit()

    return jsonify({"message": "Settings saved"}), 200

# Route only used for default profile and banner images
# @app.route("/storage/<filename>")
# def view_default(filename):
#     filepath = path.join(STORAGE_PATH, filename)
#     return send_file(filepath)

@app.route("/storage/<streamer>/<filename>")
def view_file(streamer, filename):
    filepath = path.join(STORAGE_PATH, streamer)
    fname = path.join(filepath, filename)
    defname = path.join(STORAGE_PATH, "default-"+filename)
    if path.exists(fname):
        return send_file(fname)
    else:
        return send_file(defname)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    uploadType = request.form.get('type')

    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    
    if not valid_extension(file.filename):
        return jsonify({"message": "Not a valid image file"}), 400

    img = Image.open(file)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    width, height = img.size
    if uploadType == 'profile-pic':
        if width != height:
            return jsonify({"message": "Profile picture needs to have a 1:1 aspect ratio."}), 400
        img.resize((256, 256))
        filePath = STORAGE_PATH + "/" + current_user.username + "/profile-pic.jpg"
    elif uploadType == 'offline-banner':
        aspect_ratio = width / height
        target_aspect_ratio = 16 / 9
        tolerance = 0.05

        if not abs(aspect_ratio - target_aspect_ratio) <= tolerance:
            return jsonify({"message": "Offline banner needs to have a 16:9 aspect ratio."}), 400

        img.resize((1920, 1080))
        filePath = STORAGE_PATH + "/" + current_user.username + "/offline-banner.jpg"
    else:
        return jsonify({"message": "Undefined upload type"}), 400

    if file:
        # file.save(filePath)
        img.save(filePath, format='JPEG', quality=90)
        return jsonify({"message": "File uploaded successfully"}), 200

@app.route("/logout")
def logout():
    logout_user()
    # print(request.referrer[-9:])
    # print(request.referrer[0:22])
    if request.referrer[0:22] == "http://" + HOST_NAME + ":" + str(APP_PORT) + "/" and request.referrer[-9:] == "dashboard" and len(request.referrer) > 31:
        return redirect("/")
    else:
        return redirect(request.referrer)

@app.route('/stream/<streamer>/index.m3u8')
def serve_playlist(streamer):
    user = User.query.filter_by(username=streamer).first()
    streamKey = user.streamKey
    try:
        return send_file('stream/'+streamKey+'/index.m3u8', mimetype='application/x-mpegURL')
    except:
        return "Playlist not found", 404

@app.route('/stream/<streamer>/thumbnail.jpg')
def serve_thumbnail(streamer):
    user = User.query.filter_by(username=streamer).first()
    streamKey = user.streamKey
    try:
        return send_file('stream/'+streamKey+'/thumbnail.jpg', mimetype='image/jpeg')
    except:
        return "Thumbnail not found", 404

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
    
#TODO: Write a callback for when streamer stops publishing that deletes their stream directory with the thumbnail
@app.route('/stream-done', methods=['POST'])
def done_stream():
    if request.method == 'POST':
        stream_key = request.form.get('name')
        # user = User.query.filter_by(streamKey=stream_key).first()
        path = STREAM_PATH + stream_key

        try:
            shutil.rmtree(path)
            return "Stream Contents Deleted", 200
        except OSError as e:
            print(f"Error deleting '{path}': {e}")
            return "Error Deleting Stream Contents", 400

    return "Error Deleting Stream Contents", 400

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
    # print(f"{name} joined {room}'s room")

@socketio.on("disconnect")
def disconnect():
    name = session.get("name")
    room = session.get("room")
    leave_room(room)

    if room not in rooms:
        return

    rooms[str(room)]["members"] -= 1
    # print(f"{name} has left {room}'s room")


if __name__ == "__main__":
    thread = threading.Thread(target=create_latest_thumbnails)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=APP_PORT)
