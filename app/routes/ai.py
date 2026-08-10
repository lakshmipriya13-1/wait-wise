from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.token import Token
from app.models.queue import Queue
from app.models.queue_event import QueueEvent
from app.services.ai_service import analyze_queue, generate_admin_insight, predict_queue_issue
from app.services.queue_service import get_people_ahead
from app.utils.decorators import staff_required_api
from app.utils.helpers import api_success, api_error
from app.utils.logger import logger
from app.routes.admin import calculate_dashboard_metrics

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    data = request.get_json() or {}
    message = data.get('message')
    token_id = data.get('token_id')
    
    if not message:
        return api_error("BAD_REQUEST", "Message content is required.", 400)
        
    # Fetch user's token (either requested one or their active one)
    token = None
    if token_id:
        token = Token.query.get(token_id)
        if token and token.user_id != current_user.id and not current_user.is_staff():
            return api_error("FORBIDDEN", "Unauthorized to view this token context.", 403)
    else:
        # Fallback: get current active token
        token = Token.query.filter(
            Token.user_id == current_user.id,
            Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
        ).first()
        
    # Build safe queue data payload for AI
    queue_data = {}
    if token:
        people_ahead = get_people_ahead(token)
        queue_data = {
            'queue_name': token.queue.name,
            'queue_status': token.queue.status,
            'user_token': token.formatted_token(),
            'currently_serving': f"T-{token.queue.current_token_number:03d}" if token.queue.current_token_number > 0 else "None",
            'people_ahead': people_ahead,
            'estimated_wait': token.estimated_wait_minutes,
            'average_service_time': token.queue.estimated_service_time
        }
    else:
        # If user has no active token, give general info
        queue_data = {
            'queue_name': 'No active queue',
            'queue_status': 'CLOSED',
            'user_token': 'None',
            'currently_serving': 'None',
            'people_ahead': 0,
            'estimated_wait': 0,
            'average_service_time': 0
        }
        
    try:
        response = analyze_queue(queue_data, message)
        return api_success({'response': response})
    except Exception as e:
        logger.error(f"AI chat completion error: {str(e)}")
        # Check specific errors
        if "ConnectionError" in type(e).__name__ or "unavailable" in str(e).lower():
            return api_error("AI_UNAVAILABLE", "Local AI service (Ollama) is currently unavailable. Please make sure it is running.", 503)
        return api_error("AI_ERROR", f"AI service failed: {str(e)}", 500)

@ai_bp.route('/api/ai/analyze-queue', methods=['POST'])
@login_required
def ai_analyze_queue():
    data = request.get_json() or {}
    queue_id = data.get('queue_id')
    
    if not queue_id:
        return api_error("BAD_REQUEST", "Queue ID is required.", 400)
        
    queue = Queue.query.get(queue_id)
    if not queue:
        return api_error("NOT_FOUND", f"Queue {queue_id} not found.", 404)
        
    # Get counts and metadata
    waiting_count = Token.query.filter_by(queue_id=queue_id, status='WAITING').count()
    
    queue_data = {
        'name': queue.name,
        'status': queue.status,
        'waiting_count': waiting_count,
        'avg_service_time': queue.estimated_service_time
    }
    
    # Get last 10 queue events to analyze bottleneck
    events = QueueEvent.query.filter_by(queue_id=queue_id).order_by(QueueEvent.created_at.desc()).limit(10).all()
    events_str = "\n".join([
        f"- {ev.created_at.strftime('%H:%M:%S')} {ev.event_type} (Old: {ev.old_status}, New: {ev.new_status})"
        for ev in events
    ])
    
    try:
        response = predict_queue_issue(queue_data, events_str)
        return api_success({'prediction': response})
    except Exception as e:
        logger.error(f"AI queue analysis error: {str(e)}")
        if "ConnectionError" in type(e).__name__ or "unavailable" in str(e).lower():
            return api_error("AI_UNAVAILABLE", "Local AI service (Ollama) is currently unavailable. Please make sure it is running.", 503)
        return api_error("AI_ERROR", f"AI service failed: {str(e)}", 500)

@ai_bp.route('/api/ai/admin-insight', methods=['POST'])
@staff_required_api
@login_required
def ai_admin_insight():
    data = request.get_json() or {}
    query_text = data.get('query')
    
    # Calculate active daily metrics
    metrics = calculate_dashboard_metrics()
    
    try:
        response = generate_admin_insight(metrics, query_text)
        return api_success({'insight': response})
    except Exception as e:
        logger.error(f"AI admin insight error: {str(e)}")
        if "ConnectionError" in type(e).__name__ or "unavailable" in str(e).lower():
            return api_error("AI_UNAVAILABLE", "Local AI service (Ollama) is currently unavailable. Please make sure it is running.", 503)
        return api_error("AI_ERROR", f"AI service failed: {str(e)}", 500)
