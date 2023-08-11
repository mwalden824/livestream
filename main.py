from flask import Flask, render_template, request, session, redirect, url_for, send_file
from flask_socketio import join_room, leave_room, send, SocketIO
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import random
from string import ascii_letters
from werkzeug.security import generate_password_hash, check_password_hash
from os import path

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
    # session.clear()
    # session["name"] = generate_random_username()
    # if session.get("name") is None:
    #     # Handle case where user hasn't set their name
    #     return
    
    # print("The messages are: ")
    # print(messages)
    return render_template("index.html", msgs=messages)

@app.route("/login", methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username-login')
        password = request.form.get('password-login')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                # flash('')
                print("Logged in Successfully")
                login_user(user, remember=True)
                # return redirect(url_for('home'))
                # print("User: " + str(user.username))
                session["name"] = str(user.username)
                # return 'Login Successful'
                return redirect(request.referrer)
            else:
                # flash('')
                print("Incorrect Password")
        else:
            print("Username doesn't exist")
            # flash('')

    # return render_template("index.html", msgs=messages)
    return 'Authentication Error'

@app.route("/signup", methods=['POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username-signup')
        email = request.form.get('email-signup')
        password = request.form.get('password-signup')
        password2 = request.form.get('password2-signup')

    print('TESTING 123')
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
        new_user = User(username=username, email=email, password=generate_password_hash(password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        # flash('')
        print('Account created')
        # return 'Account created'
        # return '<script>loginSuccessful();</script>'
        return redirect(request.referrer)
        # return redirect(url_for(home))
    
    # return render_template('index.html', msgs=messages)
    return 'Error in Account Creation'

@app.route("/logout")
def logout():
    logout_user()
    # TODO: reload the current page
    # return redirect(url_for(home))
    return redirect(request.referrer)

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
    # print(messages)

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
    socketio.run(app, host='0.0.0.0', port=5001)

