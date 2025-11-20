from models import db, Notification

def get_user_notifications(user_id):
    """Get notifications for a user"""
    try:
        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat()
            })

        return notification_data, 200

    except Exception as e:
        return {'error': str(e)}, 500

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get(notification_id)

        if not notification:
            return {'error': 'Notification not found'}, 404

        notification.is_read = True
        db.session.commit()

        return {'message': 'Notification marked as read'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def create_notification(user_id, title, message, notification_type):
    """Create a new notification"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )

        db.session.add(notification)
        db.session.commit()

        return notification, 201

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500
