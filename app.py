import os
from flask import Flask, jsonify, render_template
from config import Config
from database.db import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database
    db.init_app(app)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Register API Blueprints
    from routes.auth import auth_bp, auth_pages_bp
    from routes.dashboard import dashboard_bp
    from routes.projects import projects_bp
    from routes.documents import documents_bp
    from routes.analysis import analysis_bp
    from routes.tasks import tasks_bp
    from routes.decisions import decisions_bp
    from routes.risks import risks_bp
    from routes.evidence import evidence_bp
    from routes.reports import reports_bp
    from routes.approvals import approvals_bp
    from routes.acknowledgements import acknowledgements_bp
    from routes.timeline import timeline_bp
    from routes.settings import settings_bp
    from routes.pages import pages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(auth_pages_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(decisions_bp)
    app.register_blueprint(risks_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(approvals_bp)
    app.register_blueprint(acknowledgements_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(pages_bp)

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large. Maximum allowed size is 16 MB.'}), 413

    with app.app_context():
        import models.models
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    print("==================================================")
    print("   KNOWBRIDGE AI — Enterprise Handover Platform   ")
    print("   Team: Code Crushers                            ")
    print("   Server running at: http://127.0.0.1:5000       ")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
