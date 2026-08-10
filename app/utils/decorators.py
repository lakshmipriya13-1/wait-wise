from functools import wraps
from flask import abort, redirect, url_for, flash, jsonify
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash("You do not have administrative privileges to access this page.", "danger")
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_staff():
            flash("You do not have staff level permissions to access this page.", "danger")
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# REST API specific authorization decorators to return JSON responses instead of redirecting/aborting HTML
def admin_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication is required to access this resource."
                }
            }), 401
        if not current_user.is_admin():
            return jsonify({
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Admin privileges are required to access this resource."
                }
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def staff_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication is required to access this resource."
                }
            }), 401
        if not current_user.is_staff():
            return jsonify({
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Staff privileges are required to access this resource."
                }
            }), 403
        return f(*args, **kwargs)
    return decorated_function
