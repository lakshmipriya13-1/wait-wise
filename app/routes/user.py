from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.token import Token
from app.models.queue import Queue
from app.models.organization import Organization
from app.models.notification import Notification
from app.models.user import User
from app.utils.validators import validate_phone
from app.services.queue_service import get_people_ahead

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    # Get active token for the user (WAITING, CALLED, or SERVING)
    active_token = Token.query.filter(
        Token.user_id == current_user.id,
        Token.status.in_(['WAITING', 'CALLED', 'SERVING'])
    ).first()
    
    people_ahead = 0
    if active_token:
        people_ahead = get_people_ahead(active_token)
        
    # Get latest notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Get token history
    history = Token.query.filter(
        Token.user_id == current_user.id,
        Token.status.notin_(['WAITING', 'CALLED', 'SERVING'])
    ).order_by(Token.created_at.desc()).limit(5).all()
    
    # Organizations list for joining queue
    organizations = Organization.query.all()
    
    return render_template(
        'user/dashboard.html',
        active_token=active_token,
        people_ahead=people_ahead,
        notifications=notifications,
        history=history,
        organizations=organizations
    )

@user_bp.route('/token/<int:token_id>')
@login_required
def token_details(token_id):
    # Fixed get_or_450 typo -> standard Flask-SQLAlchemy 404 lookup
    token = Token.query.get_or_404(token_id)
        
    # Verify ownership or staff permissions
    if token.user_id != current_user.id and not current_user.is_staff():
        flash("You are not authorized to view this token.", "danger")
        return redirect(url_for('user.dashboard'))
        
    people_ahead = get_people_ahead(token)
    return render_template('user/token.html', token=token, people_ahead=people_ahead)

@user_bp.route('/history')
@login_required
def history():
    tokens = Token.query.filter_by(user_id=current_user.id).order_by(Token.created_at.desc()).all()
    return render_template('user/history.html', tokens=tokens)

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        
        if not name:
            flash("Name cannot be empty.", "danger")
            return render_template('user/profile.html')
            
        if phone and not validate_phone(phone):
            flash("Invalid phone number format.", "danger")
            return render_template('user/profile.html')
            
        if password and len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template('user/profile.html')

        # Update current_user directly
        current_user.name = name
        current_user.phone = phone
        
        if password:
            current_user.set_password(password)
            
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('user.profile'))
        
    return render_template('user/profile.html')