from datetime import datetime
from app.extensions import db
from app.models.queue import Queue
from app.models.token import Token
from app.models.queue_event import QueueEvent
from app.services.estimation_service import estimate_wait_time
from app.services.notification_service import create_notification

def get_people_ahead(token):
    """
    Returns the count of people ahead of the given token in its queue.
    People ahead are WAITING or CALLED tokens with a lower token number.
    """
    if token.status not in ['WAITING', 'CALLED']:
        return 0
        
    count = db.session.query(db.func.count(Token.id)).filter(
        Token.queue_id == token.queue_id,
        Token.status.in_(['WAITING', 'CALLED']),
        Token.token_number < token.token_number
    ).scalar() or 0
    return count

def recalculate_queue_estimates(queue_id):
    """
    Recalculates the estimated wait minutes for all WAITING and CALLED tokens in a queue,
    based on the number of people ahead of each token.
    Emits socket updates for affected tokens.
    """
    queue = Queue.query.get(queue_id)
    if not queue:
        return
        
    active_tokens = Token.query.filter(
        Token.queue_id == queue_id,
        Token.status.in_(['WAITING', 'CALLED'])
    ).order_by(Token.token_number).all()
    
    # Also find how many staff are active or active counters. For now default to 1
    avg_service_time = queue.estimated_service_time or 15
    
    for token in active_tokens:
        people_ahead = get_people_ahead(token)
        new_est = estimate_wait_time(people_ahead, avg_service_time)
        
        if token.estimated_wait_minutes != new_est:
            token.estimated_wait_minutes = new_est
            
            # Send dynamic notifications for changes in wait time or approaching turn
            if people_ahead == 3:
                create_notification(
                    user_id=token.user_id,
                    token_id=token.id,
                    title="Your turn is approaching!",
                    message=f"There are only 3 people ahead of you in the queue {queue.name}."
                )
    
    db.session.commit()
    emit_queue_update(queue_id)

def emit_queue_update(queue_id):
    """
    Emits a queue_updated websocket event with the latest queue state.
    """
    try:
        from app.extensions import socketio
        queue = Queue.query.get(queue_id)
        if not queue:
            return
            
        # Get count of waiting users
        waiting_count = Token.query.filter_by(queue_id=queue_id, status='WAITING').count()
        serving_token = Token.query.filter_by(queue_id=queue_id, status='SERVING').first()
        called_token = Token.query.filter_by(queue_id=queue_id, status='CALLED').first()
        
        current_serving = "None"
        if serving_token:
            current_serving = serving_token.formatted_token()
        elif called_token:
            current_serving = called_token.formatted_token()
            
        socketio.emit('queue_updated', {
            'queue_id': queue.id,
            'name': queue.name,
            'status': queue.status,
            'current_token_number': queue.current_token_number,
            'current_serving': current_serving,
            'waiting_count': waiting_count,
            'updated_at': queue.updated_at.isoformat()
        })
    except Exception as e:
        # Prevent socket emission failures from blocking core business logic
        pass

def call_next_token(queue_id):
    """
    Calls the next waiting token in the queue.
    """
    queue = Queue.query.get(queue_id)
    if not queue:
        raise ValueError("Queue not found")
        
    if queue.status != 'OPEN':
        raise ValueError(f"Queue is not open (status: {queue.status})")
        
    # Get current serving/called token and mark them completed/skipped?
    # Usually, calling next token means we complete/skip the current serving token first,
    # or the operator clicks complete/skip explicitly.
    # Let's find the next WAITING token
    next_token = Token.query.filter_by(queue_id=queue_id, status='WAITING').order_by(Token.token_number).first()
    if not next_token:
        return None
        
    # Mark previously called/serving tokens as skipped or completed? Or let the admin manage.
    # Let's transition the new token to CALLED
    old_status = next_token.status
    next_token.status = 'CALLED'
    next_token.called_at = datetime.utcnow()
    
    # Update queue's current token number
    queue.current_token_number = next_token.token_number
    
    # Log event
    event = QueueEvent(
        queue_id=queue_id,
        token_id=next_token.id,
        event_type='TOKEN_CALLED',
        old_status=old_status,
        new_status='CALLED',
        metadata_json={'token_number': next_token.token_number}
    )
    db.session.add(event)
    db.session.commit()
    
    # Notify user
    create_notification(
        user_id=next_token.user_id,
        token_id=next_token.id,
        title="Your token has been called!",
        message=f"Please proceed to the counter. Your token {next_token.formatted_token()} is being called."
    )
    
    # Emit specific socket event
    try:
        from app.extensions import socketio
        socketio.emit('token_called', next_token.to_dict())
    except:
        pass
        
    recalculate_queue_estimates(queue_id)
    return next_token

def call_token(token_id):
    """
    Calls a specific token.
    """
    token = Token.query.get(token_id)
    if not token:
        raise ValueError("Token not found")
        
    if token.status == 'COMPLETED' or token.status == 'CANCELLED':
        raise ValueError("Cannot call a completed or cancelled token")
        
    queue = token.queue
    if queue.status != 'OPEN':
        raise ValueError("Queue is not open")
        
    old_status = token.status
    token.status = 'SERVING' # transition directly to serving
    
    # Update queue's current token number
    queue.current_token_number = token.token_number
    
    event = QueueEvent(
        queue_id=queue.id,
        token_id=token.id,
        event_type='TOKEN_CALLED',
        old_status=old_status,
        new_status='SERVING',
        metadata_json={'token_number': token.token_number}
    )
    db.session.add(event)
    db.session.commit()
    
    create_notification(
        user_id=token.user_id,
        token_id=token.id,
        title="Now serving your token!",
        message=f"Your token {token.formatted_token()} is now being served."
    )
    
    recalculate_queue_estimates(queue.id)
    return token

def skip_token(token_id):
    """
    Skips the given token.
    """
    token = Token.query.get(token_id)
    if not token:
        raise ValueError("Token not found")
        
    if token.status not in ['WAITING', 'CALLED', 'SERVING']:
        raise ValueError("Can only skip waiting, called, or serving tokens")
        
    old_status = token.status
    token.status = 'SKIPPED'
    
    event = QueueEvent(
        queue_id=token.queue_id,
        token_id=token.id,
        event_type='TOKEN_SKIPPED',
        old_status=old_status,
        new_status='SKIPPED'
    )
    db.session.add(event)
    db.session.commit()
    
    create_notification(
        user_id=token.user_id,
        token_id=token.id,
        title="Your token was skipped",
        message=f"Your token {token.formatted_token()} was skipped. Contact the administrator if you missed your turn."
    )
    
    try:
        from app.extensions import socketio
        socketio.emit('token_skipped', token.to_dict())
    except:
        pass
        
    recalculate_queue_estimates(token.queue_id)
    return token

def complete_token(token_id):
    """
    Completes the given token.
    """
    token = Token.query.get(token_id)
    if not token:
        raise ValueError("Token not found")
        
    if token.status not in ['WAITING', 'CALLED', 'SERVING']:
        raise ValueError("Can only complete active tokens")
        
    old_status = token.status
    token.status = 'COMPLETED'
    token.completed_at = datetime.utcnow()
    
    event = QueueEvent(
        queue_id=token.queue_id,
        token_id=token.id,
        event_type='TOKEN_COMPLETED',
        old_status=old_status,
        new_status='COMPLETED'
    )
    db.session.add(event)
    db.session.commit()
    
    create_notification(
        user_id=token.user_id,
        token_id=token.id,
        title="Service completed",
        message=f"Thank you for using WaitWise. Your session with token {token.formatted_token()} has ended."
    )
    
    try:
        from app.extensions import socketio
        socketio.emit('token_completed', token.to_dict())
    except:
        pass
        
    recalculate_queue_estimates(token.queue_id)
    return token

def cancel_token(token_id):
    """
    Cancels the given token.
    """
    token = Token.query.get(token_id)
    if not token:
        raise ValueError("Token not found")
        
    if token.status not in ['WAITING', 'CALLED', 'SERVING']:
        raise ValueError("Can only cancel active tokens")
        
    old_status = token.status
    token.status = 'CANCELLED'
    token.cancelled_at = datetime.utcnow()
    
    event = QueueEvent(
        queue_id=token.queue_id,
        token_id=token.id,
        event_type='TOKEN_CANCELLED',
        old_status=old_status,
        new_status='CANCELLED'
    )
    db.session.add(event)
    db.session.commit()
    
    create_notification(
        user_id=token.user_id,
        token_id=token.id,
        title="Token cancelled",
        message=f"Your token {token.formatted_token()} has been cancelled."
    )
    
    try:
        from app.extensions import socketio
        socketio.emit('token_cancelled', token.to_dict())
    except:
        pass
        
    recalculate_queue_estimates(token.queue_id)
    return token

def pause_queue(queue_id):
    """
    Pauses the queue.
    """
    queue = Queue.query.get(queue_id)
    if not queue:
        raise ValueError("Queue not found")
        
    old_status = queue.status
    queue.status = 'PAUSED'
    
    event = QueueEvent(
        queue_id=queue.id,
        event_type='QUEUE_PAUSED',
        old_status=old_status,
        new_status='PAUSED'
    )
    db.session.add(event)
    
    # Notify all users currently in this queue
    waiting_tokens = Token.query.filter_by(queue_id=queue_id, status='WAITING').all()
    for token in waiting_tokens:
        create_notification(
            user_id=token.user_id,
            token_id=token.id,
            title="Queue paused",
            message=f"The queue {queue.name} has been paused temporarily."
        )
        
    db.session.commit()
    
    try:
        from app.extensions import socketio
        socketio.emit('queue_paused', {'queue_id': queue.id})
    except:
        pass
        
    emit_queue_update(queue_id)
    return queue

def resume_queue(queue_id):
    """
    Resumes the queue.
    """
    queue = Queue.query.get(queue_id)
    if not queue:
        raise ValueError("Queue not found")
        
    old_status = queue.status
    queue.status = 'OPEN'
    
    event = QueueEvent(
        queue_id=queue.id,
        event_type='QUEUE_RESUMED',
        old_status=old_status,
        new_status='OPEN'
    )
    db.session.add(event)
    
    # Notify all users currently in this queue
    waiting_tokens = Token.query.filter_by(queue_id=queue_id, status='WAITING').all()
    for token in waiting_tokens:
        create_notification(
            user_id=token.user_id,
            token_id=token.id,
            title="Queue resumed",
            message=f"The queue {queue.name} has been resumed."
        )
        
    db.session.commit()
    
    try:
        from app.extensions import socketio
        socketio.emit('queue_resumed', {'queue_id': queue.id})
    except:
        pass
        
    emit_queue_update(queue_id)
    return queue

def reset_queue(queue_id):
    """
    Resets the queue for the day: marks active tokens as EXPIRED and resets serving counter.
    """
    queue = Queue.query.get(queue_id)
    if not queue:
        raise ValueError("Queue not found")
        
    # Mark all active tokens in this queue as EXPIRED
    active_tokens = Token.query.filter(
        Token.queue_id == queue_id,
        Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
    ).all()
    
    for token in active_tokens:
        token.status = 'EXPIRED'
        event = QueueEvent(
            queue_id=queue_id,
            token_id=token.id,
            event_type='TOKEN_EXPIRED',
            old_status=token.status,
            new_status='EXPIRED'
        )
        db.session.add(event)
        
    queue.current_token_number = 0
    db.session.commit()
    
    emit_queue_update(queue_id)
    return queue
