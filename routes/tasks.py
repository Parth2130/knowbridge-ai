from flask import Blueprint, request, jsonify
from models.models import Task, Project, Activity, Dependency
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@tasks_bp.route('', methods=['GET'])
@login_required
def list_tasks():
    user = get_current_user()
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    search = request.args.get('search', '').strip().lower()

    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'tasks': [], 'overdue_tasks': []}), 200

    query = Task.query.filter(Task.project_id.in_(project_ids))

    if project_id and project_id in project_ids:
        query = query.filter_by(project_id=project_id)
    if status and status != 'All':
        query = query.filter_by(status=status)
    if priority and priority != 'All':
        query = query.filter_by(priority=priority)
    if search:
        query = query.filter(Task.description.ilike(f'%{search}%') | Task.responsible_person.ilike(f'%{search}%'))

    tasks = query.order_by(Task.created_at.desc()).all()

    # Identify overdue tasks (if deadline looks like past date or overdue string)
    overdue_tasks = []
    now = datetime.utcnow()
    for t in tasks:
        if t.status != 'Completed' and t.deadline:
            d_str = t.deadline.lower()
            if 'overdue' in d_str or 'delayed' in d_str:
                overdue_tasks.append(t.to_dict())

    return jsonify({
        'tasks': [t.to_dict() for t in tasks],
        'overdue_tasks': overdue_tasks,
        'counts': {
            'pending': len([t for t in tasks if t.status == 'Pending']),
            'in_progress': len([t for t in tasks if t.status == 'In Progress']),
            'completed': len([t for t in tasks if t.status == 'Completed']),
            'blocked': len([t for t in tasks if t.status == 'Blocked'])
        }
    }), 200

@tasks_bp.route('', methods=['POST'])
@login_required
def create_task():
    user = get_current_user()
    data = request.get_json() or {}

    project_id = data.get('project_id')
    description = data.get('description', '').strip()
    responsible_person = data.get('responsible_person', 'Unassigned').strip()
    deadline = data.get('deadline', '').strip()
    priority = data.get('priority', 'Medium')
    status = data.get('status', 'Pending')

    if not project_id or not description:
        return jsonify({'error': 'Project and task description are required.'}), 400

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    task = Task(
        project_id=project.id,
        description=description,
        responsible_person=responsible_person or 'Unassigned',
        deadline=deadline or 'Not specified',
        priority=priority,
        status=status,
        verification_status='Approved',  # User-created tasks are verified
        confidence=1.0
    )
    db.session.add(task)
    db.session.commit()

    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        user_name=user.full_name,
        activity_type='Task Added',
        description=f"Task added: '{description[:60]}...'",
        entity_type='task',
        entity_id=task.id
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({'message': 'Task created successfully.', 'task': task.to_dict()}), 201

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    user = get_current_user()
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found.'}), 404

    project = Project.query.filter_by(id=task.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Unauthorized access.'}), 403

    data = request.get_json() or {}

    old_status = task.status
    if 'description' in data and data['description'].strip():
        task.description = data['description'].strip()
    if 'responsible_person' in data:
        task.responsible_person = data['responsible_person'].strip() or 'Unassigned'
    if 'deadline' in data:
        task.deadline = data['deadline'].strip()
    if 'priority' in data:
        task.priority = data['priority']
    if 'verification_status' in data:
        task.verification_status = data['verification_status']

    # Status change handling with dependency blocking check
    if 'status' in data:
        new_status = data['status']
        # Check if moving to In Progress or Completed while blocked by unfinished prerequisite
        if new_status in ('In Progress', 'Completed'):
            blocking_deps = Dependency.query.filter_by(dependent_task_id=task.id, is_blocking=True).all()
            for dep in blocking_deps:
                if dep.prerequisite_task and dep.prerequisite_task.status != 'Completed':
                    return jsonify({
                        'error': f"Cannot set task to '{new_status}': Blocked by prerequisite task '{dep.prerequisite_task.description[:50]}' (Status: {dep.prerequisite_task.status})."
                    }), 400

        task.status = new_status
        if old_status != new_status and new_status == 'Completed':
            activity = Activity(
                project_id=project.id,
                user_id=user.id,
                user_name=user.full_name,
                activity_type='Task Completed',
                description=f"Task completed: '{task.description[:60]}'",
                entity_type='task',
                entity_id=task.id
            )
            db.session.add(activity)

    task.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Task updated successfully.', 'task': task.to_dict()}), 200

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    user = get_current_user()
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found.'}), 404

    project = Project.query.filter_by(id=task.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Unauthorized access.'}), 403

    db.session.delete(task)
    db.session.commit()

    return jsonify({'message': 'Task deleted successfully.'}), 200
