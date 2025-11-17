import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Import models and controllers
from models import db, User
from auth import init_auth, register_user, login_user, get_current_user, update_profile
from matching import find_potential_matches, create_match, get_user_matches, update_match_status
from chat import init_socket_events, get_conversation, get_unread_count, get_recent_conversations
from notifications import (
    create_notification, get_user_notifications, mark_notification_read,
    mark_all_notifications_read, get_unread_notification_count, delete_notification
)

# Flask app config
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default-secret")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default-jwt")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///roomimatch.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Extensions
CORS(app)
jwt = JWTManager(app)
db.init_app(app)

# Use THREADING instead of EVENTLET (Render safe)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Google OAuth
oauth, google = init_auth(app)

# Chat sockets
init_socket_events(socketio)

# DB table creation
def create_tables():
    with app.app_context():
        db.create_all()


# ------------- AUTH ROUTES -------------

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json()
    result, code = register_user(data)
    return jsonify(result), code


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    result, code = login_user(data)
    return jsonify(result), code


@app.route("/api/auth/google", methods=["GET"])
def google_login():
    redirect_uri = request.host_url.rstrip("/") + "/api/auth/google/callback"
    return google.authorize_redirect(redirect_uri)


@app.route("/api/auth/google/callback", methods=["GET"])
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()

    user = User.query.filter_by(email=user_info["email"]).first()

    if not user:
        user = User(
            email=user_info["email"],
            name=user_info["name"],
            profile_picture=user_info.get("picture", "")
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({
        "message": "Google login successful",
        "user": {"id": user.id, "email": user.email, "name": user.name},
        "access_token": access_token
    })


# ------------- ROOT ROUTE -------------
@app.route("/")
def index():
    return "🚀 RoomiMatch Backend is Live on Render!"


# ------------- PRODUCTION SERVER START -------------
def run():
    create_tables()
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        allow_unsafe_werkzeug=True   # REQUIRED for Render
    )


if __name__ == "__main__":
    run()
