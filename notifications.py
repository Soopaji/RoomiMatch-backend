from models import db, Notification

def create_notification(user_id, title, message, notification_type):
    """Create a new notification for a user"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        db.session.add(notification)
        db.session.commit()

        return {
            'id': notification.id,
            'title': title,
            'message': message,
            'type': notification_type,
            'is_read': False,
            'created_at': notification.created_at.isoformat()
        }, 201

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_user_notifications(user_id, page=1, per_page=20):
    """Get notifications for a user"""
    try:
        offset = (page - 1) * per_page

        notifications = Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()

        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat()
            })

        return notification_data, 200

    except Exception as e:
        return {'error': str(e)}, 500

def mark_notification_read(notification_id, user_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return {'error': 'Notification not found'}, 404

        notification.is_read = True
        db.session.commit()

        return {'message': 'Notification marked as read'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user"""
    try:
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True})

        db.session.commit()

        return {'message': 'All notifications marked as read'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

def get_unread_notification_count(user_id):
    """Get count of unread notifications for a user"""
    try:
        count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()

        return {'unread_count': count}, 200

    except Exception as e:
        return {'error': str(e)}, 500

def delete_notification(notification_id, user_id):
    """Delete a notification"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return {'error': 'Notification not found'}, 404

        db.session.delete(notification)
        db.session.commit()

        return {'message': 'Notification deleted'}, 200

    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500
