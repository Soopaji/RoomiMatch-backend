from models import db, Message, Notification, User
from flask_socketio import emit, join_room, leave_room
import json

def init_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('join')
    def handle_join(data):
        user_id = data.get('user_id')
        if user_id:
            join_room(f'user_{user_id}')
            emit('joined', {'message': f'Joined room for user {user_id}'})

    @socketio.on('leave')
    def handle_leave(data):
        user_id = data.get('user_id')
        if user_id:
            leave_room(f'user_{user_id}')
            emit('left', {'message': f'Left room for user {user_id}'})

    @socketio.on('send_message')
    def handle_send_message(data):
        try:
            sender_id = data['sender_id']
            receiver_id = data['receiver_id']
            content = data['content']
            message_type = data.get('message_type', 'text')

            # Save message to database
            message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                message_type=message_type
            )
            db.session.add(message)
            db.session.commit()

            # Create notification for receiver
            sender = User.query.get(sender_id)
            notification = Notification(
                user_id=receiver_id,
                title='New Message',
                message=f'You have a new message from {sender.name}',
                notification_type='message'
            )
            db.session.add(notification)
            db.session.commit()

            # Emit message to receiver's room
            message_data = {
                'id': message.id,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'content': content,
                'message_type': message_type,
                'is_read': False,
                'created_at': message.created_at.isoformat(),
                'sender_name': sender.name
            }

            emit('receive_message', message_data, room=f'user_{receiver_id}')
            emit('message_sent', message_data, room=f'user_{sender_id}')

        except Exception as e:
            emit('error', {'message': str(e)})

    @socketio.on('mark_messages_read')
    def handle_mark_messages_read(data):
        try:
            user_id = data['user_id']
            other_user_id = data['other_user_id']

            # Mark messages as read
            Message.query.filter(
                Message.sender_id == other_user_id,
                Message.receiver_id == user_id,
                Message.is_read == False
            ).update({'is_read': True})

            db.session.commit()

            emit('messages_marked_read', {'other_user_id': other_user_id})

        except Exception as e:
            emit('error', {'message': str(e)})

def get_conversation(user1_id, user2_id, page=1, per_page=50):
    """Get conversation between two users"""
    try:
        offset = (page - 1) * per_page

        messages = Message.query.filter(
            ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
            ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
        ).order_by(Message.created_at.desc()).offset(offset).limit(per_page).all()

        # Reverse to get chronological order
        messages.reverse()

        message_data = []
        for message in messages:
            sender = User.query.get(message.sender_id)
            message_data.append({
                'id': message.id,
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id,
                'content': message.content,
                'message_type': message.message_type,
                'is_read': message.is_read,
                'created_at': message.created_at.isoformat(),
                'sender_name': sender.name
            })

        return message_data, 200

    except Exception as e:
        return {'error': str(e)}, 500

def get_unread_count(user_id):
    """Get count of unread messages for a user"""
    try:
        count = Message.query.filter(
            Message.receiver_id == user_id,
            Message.is_read == False
        ).count()

        return {'unread_count': count}, 200

    except Exception as e:
        return {'error': str(e)}, 500

def get_recent_conversations(user_id):
    """Get recent conversations for a user"""
    try:
        # Get the latest message for each conversation
        subquery = db.session.query(
            Message.sender_id,
            Message.receiver_id,
            db.func.max(Message.created_at).label('latest_message_time')
        ).filter(
            (Message.sender_id == user_id) | (Message.receiver_id == user_id)
        ).group_by(
            db.case(
                (Message.sender_id == user_id, Message.receiver_id),
                else_=Message.sender_id
            )
        ).subquery()

        # Get the actual latest messages
        latest_messages = db.session.query(Message).join(
            subquery,
            db.and_(
                db.or_(
                    db.and_(Message.sender_id == user_id, Message.receiver_id == subquery.c.receiver_id),
                    db.and_(Message.sender_id == subquery.c.sender_id, Message.receiver_id == user_id)
                ),
                Message.created_at == subquery.c.latest_message_time
            )
        ).all()

        conversations = []
        for message in latest_messages:
            other_user_id = message.receiver_id if message.sender_id == user_id else message.sender_id
            other_user = User.query.get(other_user_id)

            # Count unread messages in this conversation
            unread_count = Message.query.filter(
                Message.sender_id == other_user_id,
                Message.receiver_id == user_id,
                Message.is_read == False
            ).count()

            conversations.append({
                'other_user': {
                    'id': other_user.id,
                    'name': other_user.name,
                    'profile_picture': other_user.profile_picture
                },
                'latest_message': {
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'is_from_me': message.sender_id == user_id
                },
                'unread_count': unread_count
            })

        # Sort by latest message time
        conversations.sort(key=lambda x: x['latest_message']['created_at'], reverse=True)

        return conversations, 200

    except Exception as e:
        return {'error': str(e)}, 500
