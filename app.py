import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from models import db
from auth import init_auth, register_user, login_user, get_current_user, update_profile
from matching import find_potential_matches, create_match, get_user_matches, update_match_status
from chat import init_socket_events, get_conversation, get_unread_count, get_recent_conversations
from notifications import (
    create_notification, get_user_notifications, mark_notification_read,
    mark_all_notifications_read, get_unread_notification_count, delete_notification
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///roomimatch.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app)
jwt = JWTManager(app)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize auth
oauth, google = init_auth(app)

# Initialize socket events
init_socket_events(socketio)

def create_tables():
    with app.app_context():
        db.create_all()

# Auth endpoints
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    result, status_code = register_user(data)
    return jsonify(result), status_code

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    result, status_code = login_user(data)
    return jsonify(result), status_code

@app.route('/api/auth/google', methods=['GET'])
def google_login():
    redirect_uri = request.url_root.rstrip('/') + '/api/auth/google/callback'
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth/google/callback', methods=['GET'])
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    # Check if user exists, if not create them
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(
            email=user_info['email'],
            name=user_info['name'],
            profile_picture=user_info.get('picture', '')
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({
        'message': 'Google login successful',
        'user': {'id': user.id, 'email': user.email, 'name': user.name},
        'access_token': access_token
    })

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def api_get_current_user():
    result, status_code = get_current_user()
    return jsonify(result), status_code

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def api_update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    result, status_code = update_profile(user_id, data)
    return jsonify(result), status_code

# Matching endpoints
@app.route('/api/matches/potential', methods=['GET'])
@jwt_required()
def api_get_potential_matches():
    user_id = get_jwt_identity()
    filters = request.args.to_dict()
    matches = find_potential_matches(user_id, filters)

    result = []
    for user, score in matches:
        result.append({
            'id': user.id,
            'name': user.name,
            'age': user.age,
            'gender': user.gender,
            'occupation': user.occupation,
            'budget': user.budget,
            'habits': json.loads(user.habits),
            'interests': json.loads(user.interests),
            'bio': user.bio,
            'location': user.location,
            'profile_picture': user.profile_picture,
            'compatibility_score': score
        })

    return jsonify(result), 200

@app.route('/api/matches', methods=['POST'])
@jwt_required()
def api_create_match():
    user_id = get_jwt_identity()
    data = request.get_json()
    data['user1_id'] = user_id
    result, status_code = create_match(data['user1_id'], data['user2_id'])
    return jsonify(result), status_code

@app.route('/api/matches', methods=['GET'])
@jwt_required()
def api_get_matches():
    user_id = get_jwt_identity()
    result, status_code = get_user_matches(user_id)
    return jsonify(result), status_code

@app.route('/api/matches/<int:match_id>/status', methods=['PUT'])
@jwt_required()
def api_update_match_status(match_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    result, status_code = update_match_status(match_id, user_id, data['status'])
    return jsonify(result), status_code

# Chat endpoints
@app.route('/api/chat/conversation/<int:other_user_id>', methods=['GET'])
@jwt_required()
def api_get_conversation(other_user_id):
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    result, status_code = get_conversation(user_id, other_user_id, page)
    return jsonify(result), status_code

@app.route('/api/chat/unread', methods=['GET'])
@jwt_required()
def api_get_unread_count():
    user_id = get_jwt_identity()
    result, status_code = get_unread_count(user_id)
    return jsonify(result), status_code

@app.route('/api/chat/recent', methods=['GET'])
@jwt_required()
def api_get_recent_conversations():
    user_id = get_jwt_identity()
    result, status_code = get_recent_conversations(user_id)
    return jsonify(result), status_code

# Notification endpoints
@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def api_get_notifications():
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    result, status_code = get_user_notifications(user_id, page)
    return jsonify(result), status_code

@app.route('/api/notifications/unread', methods=['GET'])
@jwt_required()
def api_get_unread_notification_count():
    user_id = get_jwt_identity()
    result, status_code = get_unread_notification_count(user_id)
    return jsonify(result), status_code

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def api_mark_notification_read(notification_id):
    user_id = get_jwt_identity()
    result, status_code = mark_notification_read(notification_id, user_id)
    return jsonify(result), status_code

@app.route('/api/notifications/read-all', methods=['PUT'])
@jwt_required()
def api_mark_all_notifications_read():
    user_id = get_jwt_identity()
    result, status_code = mark_all_notifications_read(user_id)
    return jsonify(result), status_code

@app.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def api_delete_notification(notification_id):
    user_id = get_jwt_identity()
    result, status_code = delete_notification(notification_id, user_id)
    return jsonify(result), status_code

@app.route('/')
def index():
    return "✅ RoomiMatch Backend is Running!"


if __name__ == '__main__':
    create_tables()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
