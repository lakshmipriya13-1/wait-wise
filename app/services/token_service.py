from app.extensions import db
from app.models.token import Token
from app.models.queue import Queue
from app.models.queue_event import QueueEvent
from app.services.estimation_service import estimate_wait_time
from datetime import datetime

def generate_token(queue_id, user_id, priority=0):
    """
    Safely generates a sequential token number for a queue.
    Uses pessimistic database locking (SELECT FOR UPDATE) on the parent Queue
    to prevent race conditions in concurrent requests.
    """
    # 1. Lock the queue row to serialize token creation for this queue
    queue = Queue.query.filter_by(id=queue_id).with_for_update().first()
    if not queue:
        raise ValueError("Queue not found")
        
    if queue.status == 'CLOSED':
        raise ValueError("Queue is closed and cannot accept new tokens")

    # 2. Find the highest token number currently in this queue
    max_token_num = db.session.query(db.func.max(Token.token_number)).filter_by(queue_id=queue_id).scalar() or 0
    next_token_num = max_token_num + 1

    # 3. Calculate initial estimated wait time
    # Before inserting, count people ahead. Since this token is WAITING, people ahead are all current WAITING or CALLED tokens.
    # We will compute the estimated wait time using the estimation service
    people_ahead = db.session.query(db.func.count(Token.id)).filter(
        Token.queue_id == queue_id,
        Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
    ).scalar() or 0
    
    avg_service_time = queue.estimated_service_time or 15
    est_wait = estimate_wait_time(people_ahead, avg_service_time)

    # 4. Create the Token
    new_token = Token(
        queue_id=queue_id,
        user_id=user_id,
        token_number=next_token_num,
        status='WAITING',
        priority=priority,
        estimated_wait_minutes=est_wait,
        created_at=datetime.utcnow()
    )
    db.session.add(new_token)
    db.session.flush() # get the token ID

    # 5. Log the QueueEvent
    event = QueueEvent(
        queue_id=queue_id,
        token_id=new_token.id,
        event_type='TOKEN_CREATED',
        old_status=None,
        new_status='WAITING',
        metadata_json={'token_number': next_token_num}
    )
    db.session.add(event)
    
    return new_token
