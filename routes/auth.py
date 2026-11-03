from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models.models import User
from database.db import db
from routes.auth_helpers import login_required, get_current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_pages_bp = Blueprint('auth_pages', __name__)

@auth_pages_bp.route('/login')
def login_page():
    if session.get('user_id'):
        return redirect(url_for('pages.dashboard_page'))
    return render_template('login.html')

@auth_pages_bp.route('/register')
def register_page():
    if session.get('user_id'):
        return redirect(url_for('pages.dashboard_page'))
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    organisation = data.get('organisation', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    role = data.get('role', 'Project Manager')

    if not full_name or not email or not organisation or not password:
        return jsonify({'error': 'All fields are required.'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email address already exists.'}), 409

    user = User(
        full_name=full_name,
        email=email,
        organisation=organisation,
        role=role
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Log in immediately
    session['user_id'] = user.id
    session['user_name'] = user.full_name
    session['user_role'] = user.role
    session['user_org'] = user.organisation

    return jsonify({
        'message': 'Registration successful.',
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email address or password.'}), 401

    session['user_id'] = user.id
    session['user_name'] = user.full_name
    session['user_role'] = user.role
    session['user_org'] = user.organisation

    return jsonify({
        'message': 'Login successful.',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    if request.path.startswith('/api/'):
        return jsonify({'message': 'Logged out successfully.'}), 200
    return redirect(url_for('auth_pages.login_page'))

@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    user = get_current_user()
    return jsonify({'user': user.to_dict()}), 200
