from flask import Blueprint, jsonify, session
from models.models import Project, Document, Task, Decision, HandoverReport, Approval, Activity, Risk
from routes.auth_helpers import login_required, get_current_user
from database.db import db

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('', methods=['GET'])
@login_required
def get_dashboard_data():
    user = get_current_user()
    user_id = user.id

    # Filter projects created by this user or accessible in organization
    projects = Project.query.filter_by(user_id=user_id).all()
    project_ids = [p.id for p in projects]

    # Metrics
    total_projects = len(projects)
    
    documents = Document.query.filter(Document.project_id.in_(project_ids)).all() if project_ids else []
    total_documents = len(documents)
    analyzed_documents = len([d for d in documents if d.processing_status == 'Analysed'])

    tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    pending_tasks = len([t for t in tasks if t.status in ('Pending', 'In Progress', 'Blocked')])
    completed_tasks = len([t for t in tasks if t.status == 'Completed'])

    reports = HandoverReport.query.filter(HandoverReport.project_id.in_(project_ids)).all() if project_ids else []
    total_reports = len(reports)

    # Pending approvals: AI-generated tasks, decisions, and draft reports awaiting human review
    pending_approvals_count = len([t for t in tasks if t.verification_status in ('AI-Generated', 'Under Review')]) + \
                             len([r for r in reports if r.status in ('Draft', 'Generated')])

    # Recent activities
    activities = Activity.query.filter(Activity.project_id.in_(project_ids)).order_by(Activity.created_at.desc()).limit(8).all() if project_ids else []

    # Latest handover report
    latest_report = HandoverReport.query.filter(HandoverReport.project_id.in_(project_ids)).order_by(HandoverReport.created_at.desc()).first() if project_ids else None

    # Chart data
    # 1. Task status distribution
    task_distribution = {
        'Completed': completed_tasks,
        'In Progress': len([t for t in tasks if t.status == 'In Progress']),
        'Pending': len([t for t in tasks if t.status == 'Pending']),
        'Blocked': len([t for t in tasks if t.status == 'Blocked'])
    }

    # 2. Document analysis status
    doc_status = {
        'Analysed': analyzed_documents,
        'Extracted': len([d for d in documents if d.processing_status == 'Extracted']),
        'Uploaded': len([d for d in documents if d.processing_status == 'Uploaded'])
    }

    # 3. Project progress list
    project_progress_list = [p.to_dict() for p in projects[:5]]

    # 4. Top pending tasks
    top_pending = [t.to_dict() for t in tasks if t.status != 'Completed'][:5]

    return jsonify({
        'metrics': {
            'total_projects': total_projects,
            'documents_analysed': analyzed_documents,
            'total_documents': total_documents,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'handover_reports': total_reports,
            'pending_approvals': pending_approvals_count
        },
        'projects': [p.to_dict() for p in projects],
        'project_progress': project_progress_list,
        'recent_activities': [a.to_dict() for a in activities],
        'latest_report': latest_report.to_dict() if latest_report else None,
        'pending_tasks_list': top_pending,
        'charts': {
            'tasks': task_distribution,
            'documents': doc_status
        }
    }), 200
