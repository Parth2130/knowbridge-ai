from flask import Blueprint, request, jsonify
from models.models import Decision, Project, Activity, Evidence
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from datetime import datetime

decisions_bp = Blueprint('decisions', __name__, url_prefix='/api/decisions')

@decisions_bp.route('', methods=['GET'])
@login_required
def list_decisions():
    user = get_current_user()
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip().lower()

    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'decisions': []}), 200

    query = Decision.query.filter(Decision.project_id.in_(project_ids))

    if project_id and project_id in project_ids:
        query = query.filter_by(project_id=project_id)
    if status and status != 'All':
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Decision.title.ilike(f'%{search}%') | Decision.description.ilike(f'%{search}%') | Decision.reason.ilike(f'%{search}%'))

    decisions = query.order_by(Decision.created_at.desc()).all()
    results = []
    for d in decisions:
        item = d.to_dict()
        evidence = Evidence.query.filter_by(entity_type='decision', entity_id=d.id).first()
        item['evidence'] = evidence.to_dict() if evidence else None
        results.append(item)

    return jsonify({'decisions': results}), 200

@decisions_bp.route('', methods=['POST'])
@login_required
def create_decision():
    user = get_current_user()
    data = request.get_json() or {}

    project_id = data.get('project_id')
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    reason = data.get('reason', '').strip()
    decision_date = data.get('decision_date', datetime.utcnow().strftime('%Y-%m-%d'))
    status = data.get('status', 'Approved')

    if not project_id or not title or not description:
        return jsonify({'error': 'Project, title, and description are required.'}), 400

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    decision = Decision(
        project_id=project.id,
        title=title,
        description=description,
        reason=reason,
        decision_date=decision_date,
        status=status,
        verification_status='Approved',
        confidence=1.0
    )
    db.session.add(decision)
    db.session.commit()

    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        user_name=user.full_name,
        activity_type='Decision Recorded',
        description=f"Decision recorded: '{title[:60]}'",
        entity_type='decision',
        entity_id=decision.id
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Decision created successfully.', 'decision': decision.to_dict()}), 201

@decisions_bp.route('/<int:decision_id>', methods=['PUT'])
@login_required
def update_decision(decision_id):
    user = get_current_user()
    decision = Decision.query.get(decision_id)
    if not decision:
        return jsonify({'error': 'Decision not found.'}), 404

    project = Project.query.filter_by(id=decision.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Unauthorized access.'}), 403

    data = request.get_json() or {}
    if 'title' in data and data['title'].strip():
        decision.title = data['title'].strip()
    if 'description' in data:
        decision.description = data['description'].strip()
    if 'reason' in data:
        decision.reason = data['reason'].strip()
    if 'decision_date' in data:
        decision.decision_date = data['decision_date'].strip()
    if 'status' in data:
        decision.status = data['status']
    if 'verification_status' in data:
        decision.verification_status = data['verification_status']

    decision.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Decision updated successfully.', 'decision': decision.to_dict()}), 200

@decisions_bp.route('/<int:decision_id>', methods=['DELETE'])
@login_required
def delete_decision(decision_id):
    user = get_current_user()
    decision = Decision.query.get(decision_id)
    if not decision:
        return jsonify({'error': 'Decision not found.'}), 404

    project = Project.query.filter_by(id=decision.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Unauthorized access.'}), 403

    db.session.delete(decision)
    db.session.commit()

    return jsonify({'message': 'Decision deleted successfully.'}), 200
