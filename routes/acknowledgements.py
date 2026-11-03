from flask import Blueprint, request, jsonify
from models.models import Acknowledgement, HandoverReport, Project, Activity
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from datetime import datetime

acknowledgements_bp = Blueprint('acknowledgements', __name__, url_prefix='/api/acknowledgements')

@acknowledgements_bp.route('', methods=['GET'])
@login_required
def list_acknowledgements():
    user = get_current_user()
    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'acknowledgements': []}), 200

    acks = Acknowledgement.query.filter(Acknowledgement.project_id.in_(project_ids)).order_by(Acknowledgement.created_at.desc()).all()
    return jsonify({'acknowledgements': [a.to_dict() for a in acks]}), 200

@acknowledgements_bp.route('', methods=['POST'])
@login_required
def acknowledge_handover():
    user = get_current_user()
    data = request.get_json() or {}

    report_id = data.get('report_id')
    comments = data.get('comments', '').strip()

    if not report_id:
        return jsonify({'error': 'Report ID is required.'}), 400

    report = HandoverReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Handover report not found.'}), 404

    project = Project.query.get(report.project_id)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404

    # Record or update acknowledgement
    ack = Acknowledgement.query.filter_by(report_id=report.id).first()
    if not ack:
        ack = Acknowledgement(
            report_id=report.id,
            project_id=project.id,
            incoming_member_id=user.id,
            incoming_member_name=user.full_name
        )
        db.session.add(ack)

    ack.status = 'Acknowledged'
    ack.comments = comments or f"Handover formally accepted and verified by {user.full_name}."
    ack.signature_date = datetime.utcnow()

    # Update report status
    report.status = 'Acknowledged'

    # Update project status
    project.status = 'Completed'

    # Log activity
    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        user_name=user.full_name,
        activity_type='Handover Acknowledged',
        description=f"Formal handover transition accepted by {user.full_name} for '{project.name}'.",
        entity_type='acknowledgement',
        entity_id=ack.id
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({
        'message': 'Handover successfully acknowledged and archived.',
        'acknowledgement': ack.to_dict()
    }), 200
