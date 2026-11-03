from flask import Blueprint, render_template, session, redirect, url_for
from routes.auth_helpers import login_required, get_current_user
from models.models import Project

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def landing_page():
    user = get_current_user()
    return render_template('index.html', user=user)

@pages_bp.route('/dashboard')
@login_required
def dashboard_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, projects=projects, active_page='dashboard')

@pages_bp.route('/projects')
@login_required
def projects_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('projects.html', user=user, projects=projects, active_page='projects')

@pages_bp.route('/documents')
@login_required
def documents_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('documents.html', user=user, projects=projects, active_page='documents')

@pages_bp.route('/analysis')
@login_required
def analysis_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('analysis.html', user=user, projects=projects, active_page='analysis')

@pages_bp.route('/timeline')
@login_required
def timeline_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('timeline.html', user=user, projects=projects, active_page='timeline')

@pages_bp.route('/decisions')
@login_required
def decisions_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('decisions.html', user=user, projects=projects, active_page='decisions')

@pages_bp.route('/tasks')
@login_required
def tasks_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('tasks.html', user=user, projects=projects, active_page='tasks')

@pages_bp.route('/approvals')
@login_required
def approvals_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('approvals.html', user=user, projects=projects, active_page='approvals')

@pages_bp.route('/reports')
@login_required
def reports_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('reports.html', user=user, projects=projects, active_page='reports')

@pages_bp.route('/knowledge')
@login_required
def knowledge_page():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template('knowledge.html', user=user, projects=projects, active_page='knowledge')

@pages_bp.route('/settings')
@login_required
def settings_page():
    user = get_current_user()
    return render_template('settings.html', user=user, active_page='settings')
