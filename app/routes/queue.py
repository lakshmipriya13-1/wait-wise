from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.queue import Queue
from app.models.organization import Organization
from app.models.service import Service
from app.models.token import Token
from app.services.token_service import generate_token
from app.services.queue_service import get_people_ahead

queue_bp = Blueprint('queue', __name__)

@queue_bp.route('/queues')
def list_queues():
    organizations = Organization.query.all()
    # Filter by selected org
    org_id = request.args.get('org_id', type=int)
    services = []
    queues = []
    
    selected_org = None
    if org_id:
        selected_org = Organization.query.get(org_id)
        if selected_org:
            services = Service.query.filter_by(organization_id=org_id, active=True).all()
            queues = Queue.query.filter_by(organization_id=org_id).all()
            
    return render_template(
        'user/queue.html',
        organizations=organizations,
        selected_org=selected_org,
        services=services,
        queues=queues
    )

@queue_bp.route('/queues/<int:queue_id>')
def queue_detail(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    # Check if user already has an active token in this queue
    active_token = None
    people_ahead = 0
    
    if current_user.is_authenticated:
        active_token = Token.query.filter(
            Token.queue_id == queue_id,
            Token.user_id == current_user.id,
            Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
        ).first()
        if active_token:
            people_ahead = get_people_ahead(active_token)
            
    # Count waiting tokens
    waiting_count = Token.query.filter_by(queue_id=queue_id, status='WAITING').count()
    
    return render_template(
        'user/queue_details.html',
        queue=queue,
        active_token=active_token,
        people_ahead=people_ahead,
        waiting_count=waiting_count
    )

@queue_bp.route('/queues/<int:queue_id>/join', methods=['POST'])
@login_required
def join_queue(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    
    # Check if user already has an active token in ANY queue (usually one active token at a time is standard)
    existing_token = Token.query.filter(
        Token.user_id == current_user.id,
        Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
    ).first()
    
    if existing_token:
        flash(f"You already have an active token: {existing_token.formatted_token()} in queue '{existing_token.queue.name}'. Please cancel or complete it before joining a new one.", "warning")
        return redirect(url_for('user.token_details', token_id=existing_token.id))
        
    try:
        token = generate_token(queue_id=queue.id, user_id=current_user.id)
        db.session.commit()
        flash(f"Successfully joined the queue! Your token number is {token.formatted_token()}.", "success")
        return redirect(url_for('user.token_details', token_id=token.id))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('queue.queue_detail', queue_id=queue_id))
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while joining the queue. Please try again.", "danger")
        return redirect(url_for('queue.queue_detail', queue_id=queue_id))