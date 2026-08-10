from app.extensions import db
from app.models.notification import Notification
from flask_socketio import emit

def create_notification(user_id, token_id, title, message, notification_type='in-app'):
    """
    Creates a notification for a user and emits it via WebSockets.
    Extensible for SMS, email, WhatsApp, or Push notifications.
    """
    notification = Notification(
        user_id=user_id,
        token_id=token_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()
    
    # Emit real-time socket notification to the specific user channel
    try:
        from app.extensions import socketio
        # Namespace room can be user_id
        socketio.emit('notification_created', notification.to_dict(), room=f"user_{user_id}")
    except Exception as e:
        # Ignore socket emit errors so backend flow doesn't break
        pass
        
    # Extensible channels
    if notification_type == 'email':
        _send_email_notification(user_id, title, message)
    elif notification_type == 'sms':
        _send_sms_notification(user_id, title, message)
        
    return notification

def _send_email_notification(user_id, title, message):
    # Placeholder for email sending integration (e.g., SendGrid, SMTP)
    pass

def _send_sms_notification(user_id, title, message):
    # Placeholder for SMS sending integration (e.g., Twilio)
    pass
