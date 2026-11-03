from flask import Blueprint, request, jsonify, session
from models.models import Project, Activity
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from datetime import datetime

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

@projects_bp.route('', methods=['GET'])
@login_required
def list_projects():
    user = get_current_user()
    search = request.args.get('search', '').strip().lower()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()

    query = Project.query.filter_by(user_id=user.id)

    if category and category != 'All':
        query = query.filter_by(category=category)
    if status and status != 'All':
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%') | Project.description.ilike(f'%{search}%'))

    projects = query.order_by(Project.created_at.desc()).all()
    return jsonify({'projects': [p.to_dict() for p in projects]}), 200

@projects_bp.route('', methods=['POST'])
@login_required
def create_project():
    user = get_current_user()
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', 'Engineering').strip()
    outgoing_member = data.get('outgoing_member', '').strip()
    incoming_member = data.get('incoming_member', '').strip()
    start_date = data.get('start_date', '')
    deadline = data.get('deadline', '')
    status = data.get('status', 'Active')

    if not name or not outgoing_member or not incoming_member:
        return jsonify({'error': 'Project Name, Outgoing Member, and Incoming Member are required.'}), 400

    project = Project(
        user_id=user.id,
        name=name,
        description=description,
        category=category,
        outgoing_member=outgoing_member,
        incoming_member=incoming_member,
        start_date=start_date,
        deadline=deadline,
        status=status
    )
    db.session.add(project)
    db.session.commit()

    # Log activity
    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        user_name=user.full_name,
        activity_type='Project Created',
        description=f"Project '{project.name}' created by {user.full_name}.",
        entity_type='project',
        entity_id=project.id
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Project created successfully.', 'project': project.to_dict()}), 201

@projects_bp.route('/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404
    return jsonify({'project': project.to_dict()}), 200

@projects_bp.route('/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    data = request.get_json() or {}
    if 'name' in data and data['name'].strip():
        project.name = data['name'].strip()
    if 'description' in data:
        project.description = data['description'].strip()
    if 'category' in data:
        project.category = data['category'].strip()
    if 'outgoing_member' in data and data['outgoing_member'].strip():
        project.outgoing_member = data['outgoing_member'].strip()
    if 'incoming_member' in data and data['incoming_member'].strip():
        project.incoming_member = data['incoming_member'].strip()
    if 'start_date' in data:
        project.start_date = data['start_date']
    if 'deadline' in data:
        project.deadline = data['deadline']
    if 'status' in data:
        project.status = data['status']

    project.updated_at = datetime.utcnow()
    db.session.commit()

    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        user_name=user.full_name,
        activity_type='Project Updated',
        description=f"Project details for '{project.name}' were updated.",
        entity_type='project',
        entity_id=project.id
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Project updated successfully.', 'project': project.to_dict()}), 200

@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    proj_name = project.name
    db.session.delete(project)
    db.session.commit()

    return jsonify({'message': f"Project '{proj_name}' and all associated data deleted successfully."}), 200
