from flask import Blueprint, request, jsonify
from models.models import Risk, Dependency, Project, Task, Activity
from database.db import db
from routes.auth_helpers import login_required, get_current_user

risks_bp = Blueprint('risks', __name__, url_prefix='/api/risks')

@risks_bp.route('', methods=['GET'])
@login_required
def list_risks():
    user = get_current_user()
    project_id = request.args.get('project_id', type=int)

    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'risks': [], 'dependencies': []}), 200

    query = Risk.query.filter(Risk.project_id.in_(project_ids))
    if project_id and project_id in project_ids:
        query = query.filter_by(project_id=project_id)

    risks = query.order_by(Risk.created_at.desc()).all()

    # Also return dependencies for the project(s)
    dep_query = Dependency.query.filter(Dependency.project_id.in_(project_ids))
    if project_id and project_id in project_ids:
        dep_query = dep_query.filter_by(project_id=project_id)
    dependencies = dep_query.all()

    return jsonify({
        'risks': [r.to_dict() for r in risks],
        'dependencies': [d.to_dict() for d in dependencies]
    }), 200

@risks_bp.route('', methods=['POST'])
@login_required
def create_risk():
    user = get_current_user()
    data = request.get_json() or {}

    project_id = data.get('project_id')
    description = data.get('description', '').strip()
    category = data.get('category', 'Technical')
    severity = data.get('severity', 'Medium')
    suggested_action = data.get('suggested_action', '').strip()
    related_task_id = data.get('related_task_id')

    if not project_id or not description:
        return jsonify({'error': 'Project and risk description are required.'}), 400

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    risk = Risk(
        project_id=project.id,
        related_task_id=related_task_id,
        description=description,
        category=category,
        severity=severity,
        suggested_action=suggested_action,
        verification_status='Approved'
    )
    db.session.add(risk)
    db.session.commit()

    return jsonify({'message': 'Risk recorded successfully.', 'risk': risk.to_dict()}), 201

@risks_bp.route('/<int:risk_id>', methods=['PUT'])
@login_required
def update_risk(risk_id):
    user = get_current_user()
    risk = Risk.query.get(risk_id)
    if not risk:
        return jsonify({'error': 'Risk not found.'}), 404

    project = Project.query.filter_by(id=risk.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Unauthorized access.'}), 403

    data = request.get_json() or {}
    if 'description' in data:
        risk.description = data['description']
    if 'category' in data:
        risk.category = data['category']
    if 'severity' in data:
        risk.severity = data['severity']
    if 'suggested_action' in data:
        risk.suggested_action = data['suggested_action']
    if 'verification_status' in data:
        risk.verification_status = data['verification_status']

    db.session.commit()
    return jsonify({'message': 'Risk updated successfully.', 'risk': risk.to_dict()}), 200

@risks_bp.route('/<int:risk_id>', methods=['DELETE'])
@login_required
def delete_risk(risk_id):
    user = get_current_user()
    risk = Risk.query.get(risk_id)
    if not risk:
        return jsonify({'error': 'Risk not found.'}), 404

    project = Project.query.filter_by(id=risk.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Unauthorized access.'}), 403

    db.session.delete(risk)
    db.session.commit()
    return jsonify({'message': 'Risk deleted successfully.'}), 200

# Dependency routes
@risks_bp.route('/dependencies', methods=['POST'])
@login_required
def create_dependency():
    user = get_current_user()
    data = request.get_json() or {}

    project_id = data.get('project_id')
    prereq_id = data.get('prerequisite_task_id')
    dep_id = data.get('dependent_task_id')
    description = data.get('description', '')
    is_blocking = data.get('is_blocking', True)

    if not project_id or not prereq_id or not dep_id:
        return jsonify({'error': 'Project, prerequisite task, and dependent task are required.'}), 400

    if prereq_id == dep_id:
        return jsonify({'error': 'A task cannot depend on itself.'}), 400

    dep = Dependency(
        project_id=project_id,
        prerequisite_task_id=prereq_id,
        dependent_task_id=dep_id,
        description=description,
        is_blocking=is_blocking
    )
    db.session.add(dep)
    db.session.commit()

    return jsonify({'message': 'Dependency linked successfully.', 'dependency': dep.to_dict()}), 201
