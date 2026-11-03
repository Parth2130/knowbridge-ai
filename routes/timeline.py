from flask import Blueprint, request, jsonify
from models.models import Activity, Project
from routes.auth_helpers import login_required, get_current_user

timeline_bp = Blueprint('timeline', __name__, url_prefix='/api/timeline')

@timeline_bp.route('', methods=['GET'])
@login_required
def get_timeline():
    user = get_current_user()
    project_id = request.args.get('project_id', type=int)

    user_projects = Project.query.filter_by(user_id=user.id).all()
    project_ids = [p.id for p in user_projects]

    if not project_ids:
        return jsonify({'activities': []}), 200

    query = Activity.query.filter(Activity.project_id.in_(project_ids))
    if project_id and project_id in project_ids:
        query = query.filter_by(project_id=project_id)

    activities = query.order_by(Activity.created_at.desc()).all()
    return jsonify({'activities': [a.to_dict() for a in activities]}), 200
