import os
import bcrypt
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from authlib.integrations.flask_client import OAuth
from models import db, User
import json

def init_auth(app):
    oauth = OAuth(app)
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'openid email profile'},
    )
    return oauth, google

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(data):
    try:
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return {'error': 'User already exists'}, 400

        # Hash password
        password_hash = hash_password(data['password'])

        # Create new user
        user = User(
            email=data['email'],
            password_hash=password_hash,
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            occupation=data['occupation'],
            budget=data['budget'],
            habits=json.dumps(data.get('habits', [])),
            interests=json.dumps(data.get('interests', [])),
            bio=data.get('bio', ''),
            location=data.get('location', '')
        )

        db.session.add(user)
        db.session.commit()

        # Create access token
        access_token = create_access_token(identity=user.id)

        return {
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            },
            'access_token': access_token
        }, 201

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def login_user(data):
    try:
        user = User.query.filter_by(email=data['email']).first()

        if not user or not check_password(data['password'], user.password_hash):
            return {'error': 'Invalid credentials'}, 401

        access_token = create_access_token(identity=user.id)

        return {
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            },
            'access_token': access_token
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500

def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return {'error': 'User not found'}, 404

        return {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'age': user.age,
            'gender': user.gender,
            'occupation': user.occupation,
            'budget': user.budget,
            'habits': json.loads(user.habits),
            'interests': json.loads(user.interests),
            'bio': user.bio,
            'location': user.location,
            'profile_picture': user.profile_picture
        }, 200

    except Exception as e:
        return {'error': str(e)}, 500

def update_profile(user_id, data):
    try:
        user = User.query.get(user_id)

        if not user:
            return {'error': 'User not found'}, 404

        # Update fields
        for field in ['name', 'age', 'gender', 'occupation', 'budget', 'bio', 'location', 'profile_picture']:
            if field in data:
                setattr(user, field, data[field])

        if 'habits' in data:
            user.habits = json.dumps(data['habits'])

        if 'interests' in data:
            user.interests = json.dumps(data['interests'])

        db.session.commit()

        return {'message': 'Profile updated successfully'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500
