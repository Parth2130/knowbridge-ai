import json
from flask import Blueprint, request, jsonify, send_file, Response
from models.models import HandoverReport, ReportVersion, Project, Activity
from database.db import db
from routes.auth_helpers import login_required, get_current_user
from services.report_generator import ReportGenerator
from io import BytesIO
from datetime import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('', methods=['GET'])
@login_required
def list_reports():
    user = get_current_user()
    project_id = request.args.get('project_id', type=int)

    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'reports': []}), 200

    query = HandoverReport.query.filter(HandoverReport.project_id.in_(project_ids))
    if project_id and project_id in project_ids:
        query = query.filter_by(project_id=project_id)

    reports = query.order_by(HandoverReport.created_at.desc()).all()
    return jsonify({'reports': [r.to_dict() for r in reports]}), 200

@reports_bp.route('', methods=['POST'])
@login_required
def generate_report():
    user = get_current_user()
    data = request.get_json() or {}

    project_id = data.get('project_id')
    title = data.get('title', '').strip()

    if not project_id:
        return jsonify({'error': 'Project selection is required.'}), 400

    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied.'}), 404

    report_title = title or f"Knowledge Handover Report — {project.name}"

    try:
        report_data = ReportGenerator.compile_report_data(project.id, user.id)
        content_json_str = json.dumps(report_data)

        # Create report record
        report = HandoverReport(
            project_id=project.id,
            user_id=user.id,
            title=report_title,
            outgoing_member=project.outgoing_member,
            incoming_member=project.incoming_member,
            summary=report_data.get('5_project_summary'),
            status='Generated',
            current_version=1,
            content_json=content_json_str
        )
        db.session.add(report)
        db.session.flush()

        # Create version 1 record
        v1 = ReportVersion(
            report_id=report.id,
            version_number=1,
            content_json=content_json_str,
            modified_by_id=user.id,
            modified_by_name=user.full_name,
            change_summary='Initial comprehensive handover report generation.'
        )
        db.session.add(v1)

        # Log activity
        activity = Activity(
            project_id=project.id,
            user_id=user.id,
            user_name=user.full_name,
            activity_type='Report Generated',
            description=f"Handover report '{report.title}' v1 generated with 16 comprehensive sections.",
            entity_type='report',
            entity_id=report.id
        )
        db.session.add(activity)
        db.session.commit()

        return jsonify({
            'message': 'Handover report generated successfully.',
            'report': report.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Failed to generate report: {str(e)}"}), 500

@reports_bp.route('/<int:report_id>', methods=['GET'])
@login_required
def get_report(report_id):
    user = get_current_user()
    report = HandoverReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found.'}), 404

    project = Project.query.filter_by(id=report.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Access denied.'}), 403

    versions = ReportVersion.query.filter_by(report_id=report.id).order_by(ReportVersion.version_number.desc()).all()

    data = report.to_dict()
    data['versions'] = [v.to_dict() for v in versions]

    return jsonify({'report': data}), 200

@reports_bp.route('/<int:report_id>/version/<int:version_num>', methods=['GET'])
@login_required
def get_report_version(report_id, version_num):
    user = get_current_user()
    report = HandoverReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found.'}), 404

    version = ReportVersion.query.filter_by(report_id=report.id, version_number=version_num).first()
    if not version:
        return jsonify({'error': f"Version {version_num} not found."}), 404

    try:
        content = json.loads(version.content_json)
    except Exception:
        content = {}

    return jsonify({
        'version': version.to_dict(),
        'content': content
    }), 200

@reports_bp.route('/<int:report_id>', methods=['PUT'])
@login_required
def update_report(report_id):
    """
    Updates report and creates a new version record while preserving past versions!
    """
    user = get_current_user()
    report = HandoverReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found.'}), 404

    project = Project.query.filter_by(id=report.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json() or {}
    change_summary = data.get('change_summary', 'Content and executive summary adjustments.')
    new_summary = data.get('summary')
    content_override = data.get('content')

    content = report.get_content()
    if new_summary:
        report.summary = new_summary
        content['5_project_summary'] = new_summary
    if content_override and isinstance(content_override, dict):
        content.update(content_override)

    report.current_version += 1
    new_version_num = report.current_version
    report.content_json = json.dumps(content)
    report.updated_at = datetime.utcnow()

    # Create new version record
    v_new = ReportVersion(
        report_id=report.id,
        version_number=new_version_num,
        content_json=report.content_json,
        modified_by_id=user.id,
        modified_by_name=user.full_name,
        change_summary=change_summary
    )
    db.session.add(v_new)

    activity = Activity(
        project_id=project.id,
        user_id=user.id,
        user_name=user.full_name,
        activity_type='Report Updated',
        description=f"Handover report updated to version {new_version_num}: '{change_summary}'",
        entity_type='report',
        entity_id=report.id
    )
    db.session.add(activity)
    db.session.commit()

    return jsonify({
        'message': f"Report updated to version {new_version_num}.",
        'report': report.to_dict()
    }), 200

@reports_bp.route('/<int:report_id>/download', methods=['GET'])
@login_required
def download_report_pdf(report_id):
    user = get_current_user()
    report = HandoverReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found.'}), 404

    project = Project.query.filter_by(id=report.project_id, user_id=user.id).first()
    if not project:
        return jsonify({'error': 'Access denied.'}), 403

    try:
        report_data = report.get_content()
        # Fallback if empty
        if not report_data:
            report_data = ReportGenerator.compile_report_data(report.project_id, user.id)

        pdf_bytes = ReportGenerator.generate_pdf(report_data)

        clean_name = "".join(c for c in report.title if c.isalnum() or c in (' ', '_', '-')).rstrip()
        filename = f"{clean_name}_v{report.current_version}.pdf"

        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f"Failed to generate PDF: {str(e)}"}), 500
