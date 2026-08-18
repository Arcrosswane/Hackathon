from functools import wraps
from flask import session, redirect, url_for, flash, render_template, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator to restrict access to users with specific roles.
    Example: @role_required('admin') or @role_required('teacher', 'employee')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('user_role', '').lower()
            allowed_normalized = [r.lower() for r in allowed_roles]
            
            # Map "employee" <-> "teacher" for authorization flexibility
            if 'teacher' in allowed_normalized and 'employee' not in allowed_normalized:
                allowed_normalized.append('employee')
            if 'employee' in allowed_normalized and 'teacher' not in allowed_normalized:
                allowed_normalized.append('teacher')

            if user_role not in allowed_normalized:
                return render_template('errors/403.html'), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission_key):
    """
    SERVER-SIDE AUTHORIZATION: Decorator to restrict access based on granular permissions.
    Example: @permission_required('students.create')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            from app.models import User
            from app.services.setting_service import has_permission

            user_id = session.get('user_id')
            current_user = User.query.get(user_id) if user_id else None

            if not current_user or not has_permission(current_user, permission_key):
                return render_template('errors/403.html'), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
