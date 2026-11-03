from functools import wraps
from flask import session, request, jsonify, redirect, url_for
from models.models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required. Please log in.'}), 401
            return redirect(url_for('auth_pages.login_page'))
        user = User.query.get(user_id)
        if not user:
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Invalid session. Please log in again.'}), 401
            return redirect(url_for('auth_pages.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None
