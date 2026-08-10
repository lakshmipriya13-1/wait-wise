from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.queue import Queue
from app.models.token import Token
from app.services.token_service import generate_token
from app.services.queue_service import (
    call_next_token, call_token, skip_token, complete_token,
    cancel_token, pause_queue, resume_queue, get_people_ahead
)
from app.utils.decorators import staff_required_api
from app.utils.helpers import api_success, api_error
from app.utils.logger import logger

api_bp = Blueprint('api', __name__)

# --- Queue Endpoints ---

@api_bp.route('/api/queues', methods=['GET'])
def get_queues():
    queues = Queue.query.all()
    return api_success([q.to_dict() for q in queues])

@api_bp.route('/api/queues/<int:queue_id>', methods=['GET'])
def get_queue(queue_id):
    queue = Queue.query.get(queue_id)
    if not queue:
        return api_error("NOT_FOUND", f"Queue {queue_id} not found.", 404)
    return api_success(queue.to_dict())

@api_bp.route('/api/queues/<int:queue_id>/tokens', methods=['POST'])
@login_required
def create_queue_token(queue_id):
    queue = Queue.query.get(queue_id)
    if not queue:
        return api_error("NOT_FOUND", f"Queue {queue_id} not found.", 404)
        
    # Check if user already has an active token
    existing = Token.query.filter(
        Token.user_id == current_user.id,
        Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
    ).first()
    if existing:
        return api_error(
            "DUPLICATE_TOKEN",
            f"You already have an active token ({existing.formatted_token()}) in queue '{existing.queue.name}'.",
            400
        )
        
    try:
        token = generate_token(queue_id=queue.id, user_id=current_user.id)
        db.session.commit()
        logger.info(f"User {current_user.email} generated token {token.token_number} via API")
        return api_success(token.to_dict(), "Token created successfully.", 201)
    except ValueError as e:
        db.session.rollback()
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        db.session.rollback()
        logger.error(f"API token generation failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not generate token.", 500)

@api_bp.route('/api/queues/<int:queue_id>/status', methods=['GET'])
def get_queue_status(queue_id):
    queue = Queue.query.get(queue_id)
    if not queue:
        return api_error("NOT_FOUND", f"Queue {queue_id} not found.", 404)
        
    waiting_count = Token.query.filter_by(queue_id=queue_id, status='WAITING').count()
    serving_token = Token.query.filter(
        Token.queue_id == queue_id,
        Token.status.in_(['CALLED', 'SERVING'])
    ).order_by(Token.called_at.desc()).first()
    
    return api_success({
        'queue_id': queue.id,
        'name': queue.name,
        'status': queue.status,
        'current_token_number': queue.current_token_number,
        'currently_serving': serving_token.formatted_token() if serving_token else None,
        'waiting_count': waiting_count,
        'average_service_time': queue.estimated_service_time
    })


# --- Token Endpoints ---

@api_bp.route('/api/tokens/<int:token_id>', methods=['GET'])
@login_required
def get_token(token_id):
    token = Token.query.get(token_id)
    if not token:
        return api_error("NOT_FOUND", f"Token {token_id} not found.", 404)
        
    # Verify owner or staff
    if token.user_id != current_user.id and not current_user.is_staff():
        return api_error("FORBIDDEN", "Unauthorized to view this token.", 403)
        
    people_ahead = get_people_ahead(token)
    
    data = token.to_dict()
    data['formatted_token'] = token.formatted_token()
    data['people_ahead'] = people_ahead
    data['queue_name'] = token.queue.name
    data['queue_status'] = token.queue.status
    
    return api_success(data)

@api_bp.route('/api/tokens/<int:token_id>/cancel', methods=['POST'])
@login_required
def cancel_queue_token(token_id):
    token = Token.query.get(token_id)
    if not token:
        return api_error("NOT_FOUND", f"Token {token_id} not found.", 404)
        
    # Verify owner or staff
    if token.user_id != current_user.id and not current_user.is_staff():
        return api_error("FORBIDDEN", "Unauthorized to cancel this token.", 403)
        
    try:
        updated_token = cancel_token(token.id)
        logger.info(f"Token {token.id} cancelled via API")
        return api_success(updated_token.to_dict(), "Token cancelled successfully.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API token cancellation failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not cancel token.", 500)

@api_bp.route('/api/tokens/<int:token_id>/check', methods=['POST'])
def check_token_status(token_id):
    token = Token.query.get(token_id)
    if not token:
        return api_error("NOT_FOUND", f"Token {token_id} not found.", 404)
        
    people_ahead = get_people_ahead(token)
    
    return api_success({
        'token_id': token.id,
        'status': token.status,
        'token_number': token.token_number,
        'formatted_token': token.formatted_token(),
        'people_ahead': people_ahead,
        'estimated_wait_minutes': token.estimated_wait_minutes
    })


# --- Admin Queue Control Endpoints ---

@api_bp.route('/api/admin/queues/<int:queue_id>/next', methods=['POST'])
@staff_required_api
def admin_call_next(queue_id):
    try:
        token = call_next_token(queue_id)
        if token:
            logger.info(f"Staff called next token {token.token_number} for queue {queue_id}")
            return api_success(token.to_dict(), f"Next token {token.formatted_token()} called.")
        else:
            return api_success(None, "No waiting tokens in the queue.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API call next failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not call next token.", 500)

@api_bp.route('/api/admin/tokens/<int:token_id>/call', methods=['POST'])
@staff_required_api
def admin_call_specific(token_id):
    try:
        token = call_token(token_id)
        logger.info(f"Staff called specific token {token.id}")
        return api_success(token.to_dict(), f"Token {token.formatted_token()} called.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API call specific failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not call token.", 500)

@api_bp.route('/api/admin/tokens/<int:token_id>/skip', methods=['POST'])
@staff_required_api
def admin_skip_token(token_id):
    try:
        token = skip_token(token_id)
        logger.info(f"Staff skipped token {token.id}")
        return api_success(token.to_dict(), f"Token {token.formatted_token()} skipped.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API skip failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not skip token.", 500)

@api_bp.route('/api/admin/tokens/<int:token_id>/complete', methods=['POST'])
@staff_required_api
def admin_complete_token(token_id):
    try:
        token = complete_token(token_id)
        logger.info(f"Staff completed token {token.id}")
        return api_success(token.to_dict(), f"Token {token.formatted_token()} completed.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API complete failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not complete token.", 500)

@api_bp.route('/api/admin/queues/<int:queue_id>/pause', methods=['POST'])
@staff_required_api
def admin_pause_queue(queue_id):
    try:
        queue = pause_queue(queue_id)
        logger.info(f"Staff paused queue {queue_id}")
        return api_success(queue.to_dict(), f"Queue '{queue.name}' paused.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API pause failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not pause queue.", 500)

@api_bp.route('/api/admin/queues/<int:queue_id>/resume', methods=['POST'])
@staff_required_api
def admin_resume_queue(queue_id):
    try:
        queue = resume_queue(queue_id)
        logger.info(f"Staff resumed queue {queue_id}")
        return api_success(queue.to_dict(), f"Queue '{queue.name}' resumed.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API resume failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not resume queue.", 500)
        
@api_bp.route('/api/admin/queues/<int:queue_id>/reset', methods=['POST'])
@staff_required_api
def admin_reset_queue(queue_id):
    from app.services.queue_service import reset_queue
    try:
        queue = reset_queue(queue_id)
        logger.info(f"Staff reset queue {queue_id}")
        return api_success(queue.to_dict(), f"Queue '{queue.name}' reset successfully.")
    except ValueError as e:
        return api_error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        logger.error(f"API reset failed: {str(e)}")
        return api_error("SERVER_ERROR", "Could not reset queue.", 500)
