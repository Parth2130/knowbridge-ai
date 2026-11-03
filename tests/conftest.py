import os
import sys
import tempfile
import pytest

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.db import db
from config import TestConfig
from models.models import User, Project

@pytest.fixture
def app():
    upload_temp_dir = tempfile.mkdtemp()
    
    class CustomTestConfig(TestConfig):
        UPLOAD_FOLDER = upload_temp_dir
        
    app = create_app(CustomTestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client, app):
    """Client with an authenticated test user session."""
    with app.app_context():
        user = User(
            full_name="Alex Chen Test",
            email="test@knowbridge.ai",
            organisation="Acme Corp Test",
            role="Project Manager"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['user_name'] = "Alex Chen Test"
        sess['user_role'] = "Project Manager"
        sess['user_org'] = "Acme Corp Test"

    return client

@pytest.fixture
def sample_project(app, auth_client):
    with app.app_context():
        user = User.query.filter_by(email="test@knowbridge.ai").first()
        proj = Project(
            user_id=user.id,
            name="Test Cloud Migration",
            description="Testing infrastructure migration",
            category="Engineering",
            outgoing_member="Sarah Jenkins",
            incoming_member="Alex Chen",
            status="Active"
        )
        db.session.add(proj)
        db.session.commit()
        return proj.id
