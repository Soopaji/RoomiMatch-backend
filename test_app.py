import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, jwt, socketio
from models import User, Match, Message, Notification
from auth import register_user, login_user, get_current_user, update_profile
from matching import find_potential_matches, create_match, get_user_matches
from chat import get_conversation, get_unread_count, get_recent_conversations
from notifications import get_user_notifications, mark_notification_read, create_notification


class TestRoomiMatchBackend(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # Authentication Tests
    def test_register_user_success(self):
        """Test successful user registration."""
        user_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'age': 25,
            'gender': 'Male',
            'occupation': 'Student',
            'budget': '₹8000'
        }

        with self.app.app_context():
            result, status_code = register_user(user_data)

        self.assertEqual(status_code, 201)
        self.assertIn('user', result)
        self.assertEqual(result['user']['email'], 'john@example.com')

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        user_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'age': 25,
            'gender': 'Male',
            'occupation': 'Student',
            'budget': '₹8000'
        }

        with self.app.app_context():
            # Register first user
            register_user(user_data)
            # Try to register again
            result, status_code = register_user(user_data)

        self.assertEqual(status_code, 400)
        self.assertIn('error', result)

    def test_login_user_success(self):
        """Test successful user login."""
        user_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'age': 25,
            'gender': 'Male',
            'occupation': 'Student',
            'budget': '₹8000'
        }

        with self.app.app_context():
            # Register user first
            register_user(user_data)

            # Login
            login_data = {
                'email': 'john@example.com',
                'password': 'password123'
            }
            result, status_code = login_user(login_data)

        self.assertEqual(status_code, 200)
        self.assertIn('access_token', result)

    def test_login_user_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }

        with self.app.app_context():
            result, status_code = login_user(login_data)

        self.assertEqual(status_code, 401)
        self.assertIn('error', result)

    # Matching Tests
    def test_find_potential_matches(self):
        """Test finding potential matches for a user."""
        with self.app.app_context():
            # Create test users
            user1 = User(
                name='John', email='john@test.com', password_hash='hash',
                age=25, gender='Male', occupation='Student', budget='₹8000'
            )
            user2 = User(
                name='Jane', email='jane@test.com', password_hash='hash',
                age=24, gender='Female', occupation='Student', budget='₹7500'
            )
            db.session.add_all([user1, user2])
            db.session.commit()

            result, status_code = find_potential_matches(user1.id)

        self.assertEqual(status_code, 200)
        self.assertIsInstance(result, list)

    def test_create_match(self):
        """Test creating a match between two users."""
        with self.app.app_context():
            # Create test users
            user1 = User(
                name='John', email='john@test.com', password_hash='hash',
                age=25, gender='Male', occupation='Student', budget='₹8000'
            )
            user2 = User(
                name='Jane', email='jane@test.com', password_hash='hash',
                age=24, gender='Female', occupation='Student', budget='₹7500'
            )
            db.session.add_all([user1, user2])
            db.session.commit()

            match_data = {
                'user1_id': user1.id,
                'user2_id': user2.id,
                'status': 'pending'
            }

            result, status_code = create_match(match_data)

        self.assertEqual(status_code, 201)
        self.assertIn('match', result)

    # Chat Tests
    def test_get_conversation(self):
        """Test retrieving conversation between two users."""
        with self.app.app_context():
            # Create test users
            user1 = User(
                name='John', email='john@test.com', password_hash='hash',
                age=25, gender='Male', occupation='Student', budget='₹8000'
            )
            user2 = User(
                name='Jane', email='jane@test.com', password_hash='hash',
                age=24, gender='Female', occupation='Student', budget='₹7500'
            )
            db.session.add_all([user1, user2])
            db.session.commit()

            result, status_code = get_conversation(user1.id, user2.id, 1, 50)

        self.assertEqual(status_code, 200)
        self.assertIn('messages', result)
        self.assertIn('pagination', result)

    def test_get_unread_count(self):
        """Test getting unread message count for a user."""
        with self.app.app_context():
            # Create test user
            user = User(
                name='John', email='john@test.com', password_hash='hash',
                age=25, gender='Male', occupation='Student', budget='₹8000'
            )
            db.session.add(user)
            db.session.commit()

            result, status_code = get_unread_count(user.id)

        self.assertEqual(status_code, 200)
        self.assertIn('unread_count', result)

    # Notification Tests
    def test_get_user_notifications(self):
        """Test getting notifications for a user."""
        with self.app.app_context():
            # Create test user
            user = User(
                name='John', email='john@test.com', password_hash='hash',
                age=25, gender='Male', occupation='Student', budget='₹8000'
            )
            db.session.add(user)
            db.session.commit()

            result, status_code = get_user_notifications(user.id)

        self.assertEqual(status_code, 200)
        self.assertIn('notifications', result)

    def test_create_notification(self):
        """Test creating a notification."""
        with self.app.app_context():
            # Create test user
            user = User(
                name='John', email='john@test.com', password_hash='hash',
                age=25, gender='Male', occupation='Student', budget='₹8000'
            )
            db.session.add(user)
            db.session.commit()

            notification_data = {
                'user_id': user.id,
                'type': 'match',
                'message': 'You have a new match!',
                'data': {'match_id': 1}
            }

            result, status_code = create_notification(notification_data)

        self.assertEqual(status_code, 201)
        self.assertIn('notification', result)

    # API Endpoint Tests
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'healthy'})

    def test_register_endpoint(self):
        """Test user registration endpoint."""
        user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123',
            'age': 25,
            'gender': 'Male',
            'occupation': 'Student',
            'budget': '₹8000'
        }

        response = self.client.post('/api/auth/register', json=user_data)
        self.assertEqual(response.status_code, 201)

        data = response.get_json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'test@example.com')

    def test_get_users_endpoint(self):
        """Test getting all users endpoint."""
        # Create a test user first
        with self.app.app_context():
            user = User(
                name='Test User', email='test@example.com', password_hash='hash',
                age=25, gender='Male', occupation='Student', budget='₹8000'
            )
            db.session.add(user)
            db.session.commit()

        response = self.client.get('/api/users')
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)


if __name__ == '__main__':
    unittest.main()
