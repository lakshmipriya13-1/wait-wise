from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.queue import Queue
from app.models.token import Token
from app.models.user import User
from app.models.service import Service
from app.models.organization import Organization
from app.utils.decorators import staff_required, admin_required
from datetime import datetime, date, timedelta

admin_bp = Blueprint('admin', __name__)

def get_today_bounds():
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    return start, end

def calculate_dashboard_metrics():
    start, end = get_today_bounds()
    
    total_active_queues = Queue.query.filter(Queue.status.in_(['OPEN', 'PAUSED'])).count()
    waiting_users = Token.query.filter_by(status='WAITING').count()
    currently_serving = Token.query.filter(Token.status.in_(['CALLED', 'SERVING'])).count()
    
    completed_today = Token.query.filter(
        Token.status == 'COMPLETED',
        Token.completed_at >= start,
        Token.completed_at <= end
    ).count()
    
    cancelled_today = Token.query.filter(
        Token.status == 'CANCELLED',
        Token.cancelled_at >= start,
        Token.cancelled_at <= end
    ).count()
    
    skipped_today = Token.query.filter(
        Token.status == 'SKIPPED',
        Token.created_at >= start,
        Token.created_at <= end
    ).count()
    
    # Calculate Average Waiting Time (created_at to called_at/completed_at)
    # We query tokens called or completed today
    tokens_served = Token.query.filter(
        Token.status.in_(['COMPLETED', 'SERVING', 'CALLED']),
        Token.called_at >= start,
        Token.called_at <= end
    ).all()
    
    wait_times = []
    service_times = []
    
    for t in tokens_served:
        if t.called_at and t.created_at:
            wait_times.append((t.called_at - t.created_at).total_seconds() / 60.0)
            
        if t.status == 'COMPLETED' and t.completed_at and t.called_at:
            service_times.append((t.completed_at - t.called_at).total_seconds() / 60.0)
            
    avg_wait = round(sum(wait_times) / len(wait_times)) if wait_times else 0
    avg_service = round(sum(service_times) / len(service_times)) if service_times else 0
    
    return {
        'total_active_queues': total_active_queues,
        'waiting_users': waiting_users,
        'currently_serving_count': currently_serving,
        'completed_today': completed_today,
        'cancelled_today': cancelled_today,
        'skipped_today': skipped_today,
        'avg_wait_time': avg_wait,
        'avg_service_time': avg_service
    }

@admin_bp.route('/admin')
@admin_bp.route('/admin/dashboard')
@staff_required
def dashboard():
    metrics = calculate_dashboard_metrics()
    
    # Fetch list of queues for quick view
    queues = Queue.query.all()
    
    return render_template(
        'admin/dashboard.html',
        metrics=metrics,
        queues=queues
    )

@admin_bp.route('/admin/queues')
@staff_required
def queues():
    queues = Queue.query.all()
    services = Service.query.all()
    organizations = Organization.query.all()
    return render_template('admin/queues.html', queues=queues, services=services, organizations=organizations)

@admin_bp.route('/admin/queues/<int:queue_id>')
@staff_required
def queue_details(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    
    # Active tokens in order
    active_tokens = Token.query.filter(
        Token.queue_id == queue_id,
        Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
    ).order_by(Token.token_number).all()
    
    # Next tokens (only WAITING status)
    next_tokens = Token.query.filter_by(
        queue_id=queue_id,
        status='WAITING'
    ).order_by(Token.token_number).limit(5).all()
    
    # Currently serving
    serving_token = Token.query.filter(
        Token.queue_id == queue_id,
        Token.status.in_(['CALLED', 'SERVING'])
    ).first()
    
    return render_template(
        'admin/queue_details.html',
        queue=queue,
        active_tokens=active_tokens,
        next_tokens=next_tokens,
        serving_token=serving_token
    )

@admin_bp.route('/admin/tokens')
@staff_required
def tokens():
    tokens = Token.query.order_by(Token.created_at.desc()).limit(100).all()
    return render_template('admin/tokens.html', tokens=tokens)

@admin_bp.route('/admin/users')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/analytics')
@staff_required
def analytics():
    metrics = calculate_dashboard_metrics()
    
    # Get hourly traffic data (tokens created per hour today)
    start, end = get_today_bounds()
    tokens_today = Token.query.filter(
        Token.created_at >= start,
        Token.created_at <= end
    ).all()
    
    hourly_counts = [0] * 24
    for t in tokens_today:
        hour = t.created_at.hour
        hourly_counts[hour] += 1
        
    return render_template('admin/analytics.html', metrics=metrics, hourly_counts=hourly_counts)

@admin_bp.route('/admin/settings')
@admin_required
def settings():
    organizations = Organization.query.all()
    services = Service.query.all()
    return render_template('admin/settings.html', organizations=organizations, services=services)

@admin_bp.route('/admin/organization/create', methods=['POST'])
@admin_required
def create_organization():
    name = request.form.get('name')
    org_type = request.form.get('organization_type')
    address = request.form.get('address')
    
    if not name or not org_type:
        flash("Organization name and type are required.", "danger")
        return redirect(url_for('admin.settings'))
        
    try:
        org = Organization(name=name, organization_type=org_type, address=address)
        db.session.add(org)
        db.session.commit()
        flash(f"Organization '{name}' created successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating organization: {str(e)}", "danger")
        
    return redirect(url_for('admin.settings'))

@admin_bp.route('/admin/service/create', methods=['POST'])
@admin_required
def create_service():
    org_id = request.form.get('organization_id', type=int)
    name = request.form.get('name')
    desc = request.form.get('description')
    avg_time = request.form.get('average_service_time', type=int, default=15)
    
    if not org_id or not name:
        flash("Organization and service name are required.", "danger")
        return redirect(url_for('admin.settings'))
        
    try:
        svc = Service(organization_id=org_id, name=name, description=desc, average_service_time=avg_time)
        db.session.add(svc)
        db.session.commit()
        flash(f"Service '{name}' created successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating service: {str(e)}", "danger")
        
    return redirect(url_for('admin.settings'))

@admin_bp.route('/admin/queue/create', methods=['POST'])
@admin_required
def create_queue():
    svc_id = request.form.get('service_id', type=int)
    name = request.form.get('name')
    est_time = request.form.get('estimated_service_time', type=int, default=15)
    
    if not svc_id or not name:
        flash("Service and queue name are required.", "danger")
        return redirect(url_for('admin.settings'))
        
    svc = Service.query.get(svc_id)
    if not svc:
        flash("Selected service does not exist.", "danger")
        return redirect(url_for('admin.settings'))
        
    try:
        q = Queue(
            organization_id=svc.organization_id,
            service_id=svc_id,
            name=name,
            status='OPEN',
            estimated_service_time=est_time
        )
        db.session.add(q)
        db.session.commit()
        flash(f"Queue counter '{name}' created successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating queue: {str(e)}", "danger")
        
    return redirect(url_for('admin.settings'))

# --- Public TV Display (No Authentication Required) ---
@admin_bp.route('/public/display/<int:queue_id>')
def public_display(queue_id):
    queue = Queue.query.get_or_404(queue_id)
    
    serving_token = Token.query.filter(
        Token.queue_id == queue_id,
        Token.status.in_(['CALLED', 'SERVING'])
    ).order_by(Token.called_at.desc()).first()
    
    next_tokens = Token.query.filter_by(
        queue_id=queue_id,
        status='WAITING'
    ).order_by(Token.token_number).limit(4).all()
    
    return render_template(
        'public/display.html',
        queue=queue,
        serving_token=serving_token,
        next_tokens=next_tokens
    )
