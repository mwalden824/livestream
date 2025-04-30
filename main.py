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
# HOST_NAME = "10.0.0.80"
HOST_NAME = "veech.lol"
STREAM_PORT = 1935
STREAM_APP_NAME = "live"
STREAM_SERVER_URL = HOST_NAME + ":" + str(STREAM_PORT)
APP_PORT = 5001
STORAGE_PATH = "storage"
STREAM_PATH = "stream/"
THUMBNAIL_CREATION_PERIOD = 15 # seconds
DEFAULT_DESCRIPTIOIN = "Streamer's description goes here."
DEFAULT_STREAM_TITLE = "Stream Title Goes Here."
DEFAULT_CATEGORY = "Chatting"

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysupersecretkeybitch"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
db = SQLAlchemy(app)
# db.init_app(app)

# Intermediate table for the many-to-many relationship
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('following_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

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
    description = db.Column(db.String(500), default=DEFAULT_DESCRIPTIOIN)
    streamTitle = db.Column(db.String(40), default=DEFAULT_STREAM_TITLE)
    category = db.Column(db.String(20), default=DEFAULT_CATEGORY)
    streamTags = db.Column(db.String(40), default="")

    followers = db.relationship('User', secondary=followers, primaryjoin=(followers.c.follower_id == id), secondaryjoin=(followers.c.following_id == id), backref=db.backref('following', lazy='dynamic'), lazy='dynamic')

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
liveStreamers = []

def valid_extension(filename):
    _, extension = path.splitext(filename)
    valid_extensions = ['.png', '.jpg', '.jpeg']
    
    if extension.lower() in valid_extensions:
        return True
    else:
        return False

def create_latest_thumbnails():
    global liveStreamers
    while True:
        for folder_name in listdir(STREAM_PATH):
            folder_path = path.join(STREAM_PATH, folder_name)

            with app.app_context():
                user = User.query.filter_by(streamKey=folder_name).first()
                if user not in liveStreamers:
                    liveStreamers.append(user)

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
                        if user in liveStreamers:
                            liveStreamers.remove(user)
                    except OSError as e:
                        print(f"Error deleting '{path}': {e}")

        time.sleep(THUMBNAIL_CREATION_PERIOD)

@app.route("/streamers_update", methods=['POST'])
# @login_required
def streamers_update():
    global liveStreamers
    onlineStreamList = []
    offlineStreamList = []
    if current_user.is_authenticated:
        following = current_user.following.all()

        for i, followed in enumerate(following):
            if i > 10:
                break
            if followed in liveStreamers:
                print("Added follower to onlineStreamList")
                onlineStreamList.append(followed.username)
            else:
                offlineStreamList.append(followed.username)

        return jsonify(online=onlineStreamList, offline=offlineStreamList), 200
    else:
        # Return list of online streamers clipped to 10 for now
        for i, streamer in enumerate(liveStreamers):
            if i > 10:
                break
            onlineStreamList.append(streamer.username)

        return jsonify(online=onlineStreamList), 200

@app.route("/", methods=["POST", "GET"])
def home():
    online_streamers = []
    for folder_name in listdir(STREAM_PATH):
        folder_path = path.join(STREAM_PATH, folder_name)
        tn_path = path.join(folder_path, "thumbnail.jpg")
        if path.isdir(folder_path) and path.exists(tn_path):
            user = User.query.filter_by(streamKey=folder_name).first()
            username = user.username
            online_streamers.append((username, user.streamTitle))

    return render_template("home.html", streamers_online=online_streamers)

@app.route("/<streamer>", methods=["POST", "GET"])
def streamname(streamer):
    user = User.query.filter_by(username=streamer).first()
    if user:
        followers = user.followers.all()
        num_followers = len(followers)
        showFollowSub = True
        isFollowing = False
        if current_user.is_authenticated:
            if user in current_user.following.all():
                isFollowing = True
            else:
                isFollowing = False
            if user == current_user:
                showFollowSub = False
        else:
            showFollowSub = False

        session["room"] = str(streamer)
        if str(streamer) not in rooms:
            # session["room"] = str(streamer)
            rooms[str(streamer)] = {"members": 0, "messages": [], "users": []}

        return render_template(
            "streamer.html", 
            msgs=rooms[streamer]["messages"], 
            viewers=str(rooms[streamer]["members"]),
            username=streamer, 
            userDescription=user.description,
            smLinks=[user.youtubeUrl, user.twitterUrl, user.instagramUrl, user.discordUrl, user.tiktokUrl],
            followed=isFollowing,
            showFollowSubBtn=showFollowSub,
            followerCount=str(num_followers),
            title_of_stream=user.streamTitle,
            tags_of_stream=user.streamTags,
            category_of_stream=user.category)
    else:
        return render_template("no-account.html", username=streamer)

@app.route('/follow/<streamer>', methods=['POST'])
@login_required
def follow(streamer):
    target_user = User.query.filter_by(username=streamer).first()
    if target_user:
        if target_user == current_user:
            return jsonify({"message": "User can't follow theirself"}), 420
        target_user.followers.append(current_user)
        db.session.commit()

        # print("FOLLOW: Current user is following: ")
        # for usern in current_user.following.all():
        #     print(str(usern.username))

        # print("FOLLOW: Target user is following: ")
        # for usern in target_user.following.all():
        #     print(str(usern.username))

        return jsonify({"message": "Successfully Added Follow"}), 200

    return jsonify({"message": "Target Username Does Not Exist"}), 404

@app.route('/unfollow/<streamer>', methods=['POST'])
@login_required
def unfollow(streamer):
    target_user = User.query.filter_by(username=streamer).first()
    if target_user:
        target_user.followers.remove(current_user)
        db.session.commit()

        # print("UNFOLLOW: Current user is following: ")
        # for usern in current_user.following.all():
        #     print(str(usern.username))

        # print("UNFOLLOW: Target user is following: ")
        # for usern in target_user.following.all():
        #     print(str(usern.username))

        return jsonify({"message": "Successfully Deleted Follow"}), 200

    return jsonify({"message": "Target Username Does Not Exist"}), 404

@app.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data["username-login"]
        password = data["password-login"]

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                print("Logged in Successfully")
                login_user(user, remember=True)
                session["name"] = str(user.username)
                return redirect(request.referrer), 200
            else:
                print("Incorrect Password")
                return jsonify({"message": "Incorrect password"}), 406
        else:
            print("Username doesn't exist")
            return jsonify({"message": "Username doesn't exist"}), 404

    return jsonify({"message": "Authentication Error"}), 400

@app.route("/signup", methods=['POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data["username-signup"]
        email = data["email-signup"]
        password = data["password-signup"]
        password2 = data["password2-signup"]

        user = User.query.filter_by(email=email).first()
        if user:
            print('Email already exists')
            return jsonify({"message": "Email already exists."}), 409
        elif len(email) < 4:
            print('Email too short')
            return jsonify({"message": "Email too short."}), 407
        elif len(username) < 4:
            print('Username too short')
            return jsonify({"message": "Username too short."}), 405
        elif password != password2:
            print("Passwords don't match")
            return jsonify({"message": "Passwords don't match."}), 403
        elif len(password) < 8:
            print('password too short')
            return jsonify({"message": "Password too short."}), 401
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
            return redirect(request.referrer), 200

    return jsonify({"message": "Signup Error"}), 400

@app.route("/<streamer>/dashboard")
@login_required
def dashboard(streamer):
    user = User.query.filter_by(username=streamer).first()
    if user:
        if user.username == current_user.username:
            session["room"] = str(streamer)
            if str(streamer) not in rooms:
                # session["room"] = str(streamer)
                rooms[str(streamer)] = {"members": 0, "messages": [], "users": []}
            return render_template(
                "dashboard.html",
                msgs=rooms[streamer]["messages"], 
                users=rooms[streamer]["users"], 
                stream_title=user.streamTitle,
                stream_tags=user.streamTags,
                stream_category=user.category,
                username=user.username)
        else:
            return render_template("access-denied.html", attempted_username=user.username, actual_username=current_user.username)
    else:
        return render_template("no-account.html", username=streamer)

@app.route("/<streamer>/settings")
@login_required
def settings(streamer):
    user = User.query.filter_by(username=streamer).first()
    if user:
        if user.username == current_user.username:
            return render_template(
                "settings.html", 
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

@app.route("/save_stream_settings", methods=['POST'])
@login_required
def save_stream_settings():
    data = request.json
    user = User.query.filter_by(username=current_user.username).first()

    # print(data)

    user.streamTitle = data["sTitle"]
    user.streamTags = data["sTags"]
    user.category = data["sCategory"]

    db.session.commit()

    return jsonify({"message": "Settings saved"}), 200

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
    overlay = Image.open(STORAGE_PATH + "/default-profile-pic-offline-overlay.png")
    overlay = overlay.resize((256, 256))
    width, height = img.size
    if uploadType == 'profile-pic':
        if width != height:
            return jsonify({"message": "Profile picture needs to have a 1:1 aspect ratio."}), 400
        img = img.resize((256, 256))
        filePath = STORAGE_PATH + "/" + current_user.username + "/profile-pic.jpg"

        # Create Offline profile Pic
        filePathOffline = STORAGE_PATH + "/" + current_user.username + "/profile-pic-offline.jpg"

        if img.mode != 'RGB':
            img = img.convert('RGB')
        if file:
            img.save(filePath, format='JPEG', quality=90)

            img = img.convert("L")
            img = img.convert('RGBA')
            overlay = overlay.convert('RGBA')
            img.paste(overlay, (0, 0), overlay)
            img = img.convert('RGB')
            img.save(filePathOffline, format='JPEG', quality=90)

            return jsonify({"message": "File uploaded successfully"}), 200
    elif uploadType == 'offline-banner':
        if img.mode != 'RGB':
            img = img.convert('RGB')

        aspect_ratio = width / height
        target_aspect_ratio = 16 / 9
        tolerance = 0.05

        if not abs(aspect_ratio - target_aspect_ratio) <= tolerance:
            return jsonify({"message": "Offline banner needs to have a 16:9 aspect ratio."}), 400

        img.resize((1920, 1080))
        filePath = STORAGE_PATH + "/" + current_user.username + "/offline-banner.jpg"

        if file:
            img.save(filePath, format='JPEG', quality=90)
            return jsonify({"message": "File uploaded successfully"}), 200
    else:
        return jsonify({"message": "Undefined upload type"}), 400

@app.route("/logout")
def logout():
    logout_user()
    refUrl = request.referrer[7:]
    refUrlSplit = refUrl.split("/")

    if (len(refUrlSplit) == 3) and ((refUrlSplit[2] == "dashboard") or (refUrlSplit[2] == "settings")):
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
    global liveStreamers
    if request.method == 'POST':
        stream_key = request.form.get('name')
        user = User.query.filter_by(streamKey=stream_key).first()
        if user:
            liveStreamers.append(user)
            return "Stream Allowed", 200
        else:
            return "Stream Denied", 406
    else:
        return "Error", 404

@app.route('/stream-done', methods=['POST'])
def done_stream():
    global liveStreamers
    if request.method == 'POST':
        stream_key = request.form.get('name')
        user = User.query.filter_by(streamKey=stream_key).first()

        path = STREAM_PATH + stream_key

        try:
            shutil.rmtree(path)
            liveStreamers.remove(user)
            return "Stream Contents Deleted", 200
        except OSError as e:
            print(f"Error deleting '{path}': {e}")
            return "Error Deleting Stream Contents", 400

    return "Error Deleting Stream Contents", 400

@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query')
        results = db.session.query(User).filter(
            (
                User.username.like(f"%{query}%") |
                User.streamTitle.like(f"%{query}%") |
                User.streamTags.like(f"%{query}%") |
                User.category.like(f"%{query}%") |
                User.description.like(f"%{query}%")
            )
        ).all()

        search_results = []
        for result in results:
            if result in liveStreamers:
                search_results.append((result.username, True, result.streamTitle))
            else:
                search_results.append((result.username, False, result.description))

        return render_template("search.html", searchResult=search_results), 200

    return "Error with Search", 400


@app.route('/search/<tag>', methods=['GET'])
def tag_search(tag):
    results = db.session.query(User).filter(
        (
            User.streamTags.like(f"%{tag}%")
        )
    ).all()

    search_results = []
    for result in results:
        if result in liveStreamers:
            search_results.append((result.username, True, result.streamTitle))
        else:
            search_results.append((result.username, False, result.description))

    return render_template("search.html", searchResult=search_results), 200

@socketio.on("message")
def message(data):
    room = session.get("room")
    content = {
        "type": "chat",
        "name": session.get("name"),
        "action": "message",
        "message": data["data"]
    }

    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    name = session.get("name")
    room = session.get("room")
    join_room(room)

    if room not in rooms:
        return

    if not current_user.is_authenticated:
        rooms[str(room)]["members"] += 1
        # Update live viewer count
        content = {
            "type": "count",
            "name": "anonymous",
            "action": "add",
            "message": rooms[str(room)]["members"]
        }
        send(content, to=room)
        return
    
    rooms[str(room)]["members"] += 1
    rooms[str(room)]["users"].append(name)
    # print(f"{name} joined {room}'s room")

    # Update live viewer count
    content = {
        "type": "count",
        "name": str(name),
        "action": "add",
        "message": rooms[str(room)]["members"]
    }
    send(content, to=room)


@socketio.on("disconnect")
def disconnect():
    name = session.get("name")
    room = session.get("room")
    leave_room(room)

    if room not in rooms:
        return

    if not current_user.is_authenticated:
        rooms[str(room)]["members"] -= 1
        # Update live viewer count
        content = {
            "type": "count",
            "name": "anonymous",
            "action": "remove",
            "message": rooms[str(room)]["members"]
        }
        send(content, to=room)
        return

    rooms[str(room)]["members"] -= 1
    rooms[str(room)]["users"].remove(name)
    # print(f"{name} has left {room}'s room")

    # Update live viewer count
    content = {
        "type": "count",
        "name": str(name),
        "action": "remove",
        "message": rooms[str(room)]["members"]
    }
    send(content, to=room)


if __name__ == "__main__":
    thread = threading.Thread(target=create_latest_thumbnails)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=APP_PORT)
