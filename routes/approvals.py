from flask import Blueprint, request, jsonify
from models.models import Approval, Task, Decision, Risk, HandoverReport, Project, Activity
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from datetime import datetime

approvals_bp = Blueprint('approvals', __name__, url_prefix='/api/approvals')

@approvals_bp.route('', methods=['GET'])
@login_required
def list_approvals():
    user = get_current_user()
    project_id = request.args.get('project_id', type=int)

    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'pending_items': [], 'recent_approvals': []}), 200

    # Collect pending items (tasks, decisions, risks that are AI-Generated or Under Review)
    task_q = Task.query.filter(Task.project_id.in_(project_ids), Task.verification_status.in_(['AI-Generated', 'Under Review']))
    dec_q = Decision.query.filter(Decision.project_id.in_(project_ids), Decision.verification_status.in_(['AI-Generated', 'Under Review']))
    risk_q = Risk.query.filter(Risk.project_id.in_(project_ids), Risk.verification_status.in_(['AI-Generated', 'Under Review']))

    if project_id and project_id in project_ids:
        task_q = task_q.filter_by(project_id=project_id)
        dec_q = dec_q.filter_by(project_id=project_id)
        risk_q = risk_q.filter_by(project_id=project_id)

    pending_items = []
    for t in task_q.all():
        item = t.to_dict()
        item['type'] = 'task'
        pending_items.append(item)

    for d in dec_q.all():
        item = d.to_dict()
        item['type'] = 'decision'
        pending_items.append(item)

    for r in risk_q.all():
        item = r.to_dict()
        item['type'] = 'risk'
        pending_items.append(item)

    # Approved/Rejected history
    recent_approvals = Approval.query.order_by(Approval.created_at.desc()).limit(20).all()

    return jsonify({
        'pending_items': pending_items,
        'recent_approvals': [a.to_dict() for a in recent_approvals]
    }), 200

@approvals_bp.route('/<int:entity_id>', methods=['POST'])
@login_required
def process_approval(entity_id):
    """
    Approve, Reject, or Edit AI-generated item.
    """
    user = get_current_user()
    data = request.get_json() or {}

    entity_type = data.get('entity_type', 'task').lower()
    action = data.get('action', 'Approve')  # Approve, Reject, Edit
    comments = data.get('comments', '').strip()
    edited_data = data.get('edited_data')

    project_id = None
    target_name = ""

    if entity_type == 'task':
        task = Task.query.get(entity_id)
        if not task:
            return jsonify({'error': 'Task not found.'}), 404
        project_id = task.project_id
        target_name = task.description

        if action == 'Approve':
            task.verification_status = 'Approved'
        elif action == 'Reject':
            task.verification_status = 'Rejected'
        elif action == 'Edit':
            if edited_data:
                if 'description' in edited_data:
                    task.description = edited_data['description']
                if 'responsible_person' in edited_data:
                    task.responsible_person = edited_data['responsible_person']
                if 'deadline' in edited_data:
                    task.deadline = edited_data['deadline']
            task.verification_status = 'Approved'

    elif entity_type == 'decision':
        dec = Decision.query.get(entity_id)
        if not dec:
            return jsonify({'error': 'Decision not found.'}), 404
        project_id = dec.project_id
        target_name = dec.title

        if action == 'Approve':
            dec.verification_status = 'Approved'
        elif action == 'Reject':
            dec.verification_status = 'Rejected'
        elif action == 'Edit':
            if edited_data:
                if 'title' in edited_data:
                    dec.title = edited_data['title']
                if 'reason' in edited_data:
                    dec.reason = edited_data['reason']
            dec.verification_status = 'Approved'

    elif entity_type == 'risk':
        risk = Risk.query.get(entity_id)
        if not risk:
            return jsonify({'error': 'Risk not found.'}), 404
        project_id = risk.project_id
        target_name = risk.description

        if action == 'Approve':
            risk.verification_status = 'Approved'
        elif action == 'Reject':
            risk.verification_status = 'Rejected'

    elif entity_type == 'report':
        rep = HandoverReport.query.get(entity_id)
        if not rep:
            return jsonify({'error': 'Report not found.'}), 404
        project_id = rep.project_id
        target_name = rep.title

        if action == 'Approve':
            rep.status = 'Approved'
        elif action == 'Reject':
            rep.status = 'Draft'

    # Save approval record
    approval = Approval(
        entity_type=entity_type,
        entity_id=entity_id,
        reviewer_id=user.id,
        reviewer_name=user.full_name,
        action=action,
        comments=comments or f"Human reviewer marked as {action}."
    )
    db.session.add(approval)

    # Log activity
    if project_id:
        activity = Activity(
            project_id=project_id,
            user_id=user.id,
            user_name=user.full_name,
            activity_type=f"Information {action}d",
            description=f"{user.full_name} processed verification ({action}) on {entity_type}: '{target_name[:50]}'",
            entity_type=entity_type,
            entity_id=entity_id
        )
        db.session.add(activity)

    db.session.commit()

    return jsonify({
        'message': f"Item successfully marked as {action}d.",
        'approval': approval.to_dict()
    }), 200
