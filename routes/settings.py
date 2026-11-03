import os
from flask import Blueprint, request, jsonify, session, current_app
from models.models import User
from database.db import db
from routes.auth_helpers import login_required, get_current_user

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])
@login_required
def get_settings():
    user = get_current_user()
    has_gemini = bool(current_app.config.get('GEMINI_API_KEY'))
    has_openai = bool(current_app.config.get('OPENAI_API_KEY'))
    
    return jsonify({
        'user': user.to_dict(),
        'ai_configuration': {
            'gemini_configured': has_gemini,
            'openai_configured': has_openai,
            'active_engine': 'Gemini Cloud LLM' if has_gemini else ('OpenAI LLM' if has_openai else 'Local Deterministic NLP Engine'),
            'mode_description': 'High-precision local NLP extraction active. No external API keys required.' if not (has_gemini or has_openai) else 'Cloud LLM reasoning active.'
        }
    }), 200

@settings_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user = get_current_user()
    data = request.get_json() or {}

    full_name = data.get('full_name', '').strip()
    organisation = data.get('organisation', '').strip()
    role = data.get('role')

    if not full_name or not organisation:
        return jsonify({'error': 'Full name and organisation are required.'}), 400

    user.full_name = full_name
    user.organisation = organisation
    
    # Only allow role update if administrator or self-demo role switch
    if role in ('Administrator', 'Project Manager', 'Team Member'):
        user.role = role

    db.session.commit()
    session['user_name'] = user.full_name
    session['user_role'] = user.role
    session['user_org'] = user.organisation

    return jsonify({'message': 'Profile updated successfully.', 'user': user.to_dict()}), 200

@settings_bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    user = get_current_user()
    data = request.get_json() or {}

    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required.'}), 400

    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect.'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match.'}), 400

    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters.'}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Password changed successfully.'}), 200
