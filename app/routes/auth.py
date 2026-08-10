from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.utils.validators import validate_email, validate_phone, validate_password_strength
from app.utils.logger import logger
from app.utils.helpers import api_success, api_error

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role', 'USER')
        
        # Validation
        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template('register.html')
            
        if not validate_email(email):
            flash("Invalid email format.", "danger")
            return render_template('register.html')
            
        if not validate_phone(phone):
            flash("Invalid phone number format.", "danger")
            return render_template('register.html')
            
        if not validate_password_strength(password):
            flash("Password must be at least 6 characters.", "danger")
            return render_template('register.html')
            
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return render_template('register.html')
            
        # Create User
        try:
            user = User(name=name, email=email, phone=phone, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User registered: {email} as {role}")
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed for {email}: {str(e)}")
            flash("An error occurred during registration. Please try again.", "danger")
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template('login.html')
            
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template('login.html')
            
        if not user.is_active:
            flash("This account has been deactivated.", "danger")
            return render_template('login.html')
            
        login_user(user, remember=remember)
        logger.info(f"User logged in: {email}")
        
        # Redirect to target or dashboard
        next_page = request.args.get('next')
        if user.is_staff():
            return redirect(next_page or url_for('admin.dashboard'))
        return redirect(next_page or url_for('user.dashboard'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    email = current_user.email
    logout_user()
    logger.info(f"User logged out: {email}")
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))


# --- REST API Endpoints ---

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    role = data.get('role', 'USER')
    
    if not name or not email or not password:
        return api_error("BAD_REQUEST", "Name, email, and password are required.", 400)
        
    if not validate_email(email):
        return api_error("INVALID_EMAIL", "Invalid email format.", 400)
        
    if not validate_phone(phone):
        return api_error("INVALID_PHONE", "Invalid phone format.", 400)
        
    if not validate_password_strength(password):
        return api_error("WEAK_PASSWORD", "Password must be at least 6 characters.", 400)
        
    if User.query.filter_by(email=email).first():
        return api_error("EMAIL_EXISTS", "Email is already registered.", 400)
        
    try:
        user = User(name=name, email=email, phone=phone, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered via API: {email}")
        return api_success(user.to_dict(), "Registration successful.", 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"API registration error: {str(e)}")
        return api_error("SERVER_ERROR", "Internal server error during registration.", 500)

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    remember = bool(data.get('remember', False))
    
    if not email or not password:
        return api_error("BAD_REQUEST", "Email and password are required.", 400)
        
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return api_error("INVALID_CREDENTIALS", "Invalid email or password.", 401)
        
    if not user.is_active:
        return api_error("DEACTIVATED", "Account is inactive.", 403)
        
    login_user(user, remember=remember)
    logger.info(f"User logged in via API: {email}")
    return api_success(user.to_dict(), "Login successful.")

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    email = current_user.email
    logout_user()
    logger.info(f"User logged out via API: {email}")
    return api_success(None, "Logout successful.")

@auth_bp.route('/api/auth/me', methods=['GET'])
def api_me():
    if not current_user.is_authenticated:
        return api_error("UNAUTHORIZED", "Not authenticated", 401)
    return api_success(current_user.to_dict())
