from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.models.organization import Organization
from app.models.queue import Queue

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # If logged in, redirect to respective dashboard
    if current_user.is_authenticated:
        if current_user.is_staff():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
        
    organizations = Organization.query.all()
    queues = Queue.query.all()
    
    return render_template(
        'index.html',
        organizations=organizations,
        queues=queues
    )
