import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_socketio import SocketIO
from models import db
from auth import init_auth, register_user, login_user, get_current_user, update_profile
from matching import find_potential_matches, create_match, get_user_matches
from chat import init_socket_events, get_conversation, get_unread_count, get_recent_conversations
from notifications import get_user_notifications, mark_notification_read
import json

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///roomimatch.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')

# Initialize extensions
CORS(app)
db.init_app(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Initialize auth
oauth, google = init_auth(app)

# Initialize socket events
init_socket_events(socketio)

# Create database tables
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Database initialization error: {e}")
        pass

# Auth routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    result, status_code = register_user(data)
    return jsonify(result), status_code

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    result, status_code = login_user(data)
    return jsonify(result), status_code

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    result, status_code = get_current_user()
    return jsonify(result), status_code

@app.route('/api/auth/update-profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    data = request.get_json()
    user_id = get_jwt_identity()
    result, status_code = update_profile(user_id, data)
    return jsonify(result), status_code

# User routes
@app.route('/api/users', methods=['GET'])
def api_get_users():
    try:
        users = User.query.all()
        user_data = []
        for user in users:
            user_data.append({
                'id': user.id,
                'name': user.name,
                'age': user.age,
                'gender': user.gender,
                'occupation': user.occupation,
                'budget': user.budget,
                'habits': json.loads(user.habits) if user.habits else [],
                'interests': json.loads(user.interests) if user.interests else [],
                'bio': user.bio,
                'location': user.location,
                'profile_picture': user.profile_picture
            })
        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Matching routes
@app.route('/api/matches/potential', methods=['GET'])
@jwt_required()
def get_matches():
    result, status_code = find_potential_matches()
    return jsonify(result), status_code

@app.route('/api/matches', methods=['POST'])
@jwt_required()
def create_new_match():
    data = request.get_json()
    result, status_code = create_match(data)
    return jsonify(result), status_code

@app.route('/api/matches', methods=['GET'])
@jwt_required()
def get_matches_list():
    result, status_code = get_user_matches()
    return jsonify(result), status_code

# Chat routes
@app.route('/api/chat/conversation/<int:user2_id>', methods=['GET'])
@jwt_required()
def get_chat_conversation(user2_id):
    user1_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    result, status_code = get_conversation(user1_id, user2_id, page, per_page)
    return jsonify(result), status_code

@app.route('/api/chat/unread-count', methods=['GET'])
@jwt_required()
def get_unread_message_count():
    user_id = get_jwt_identity()
    result, status_code = get_unread_count(user_id)
    return jsonify(result), status_code

@app.route('/api/chat/recent-conversations', methods=['GET'])
@jwt_required()
def get_recent_chats():
    user_id = get_jwt_identity()
    result, status_code = get_recent_conversations(user_id)
    return jsonify(result), status_code

# Notification routes
@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    result, status_code = get_user_notifications(user_id)
    return jsonify(result), status_code

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(notification_id):
    result, status_code = mark_notification_read(notification_id)
    return jsonify(result), status_code

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    socketio.run(app, debug=os.getenv('FLASK_ENV') != 'production', host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), allow_unsafe_werkzeug=True)
