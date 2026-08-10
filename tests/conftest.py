import pytest
import sys
import os

# Ensure waitwise root directory is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.organization import Organization
from app.models.service import Service
from app.models.queue import Queue
from app.models.token import Token

@pytest.fixture
def app():
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        # Seed basic testing variables
        admin = User(name="Admin", email="admin@test.com", role="ADMIN", is_active=True)
        admin.set_password("pass123")
        
        staff = User(name="Staff", email="staff@test.com", role="STAFF", is_active=True)
        staff.set_password("pass123")
        
        user = User(name="User", email="user@test.com", role="USER", is_active=True)
        user.set_password("pass123")
        
        db.session.add_all([admin, staff, user])
        
        # Add basic org and queue
        org = Organization(name="Test Org", organization_type="Hospital")
        db.session.add(org)
        db.session.commit()
        
        svc = Service(organization_id=org.id, name="Test Service", average_service_time=15)
        db.session.add(svc)
        db.session.commit()
        
        q = Queue(organization_id=org.id, service_id=svc.id, name="Test Queue", status="OPEN", estimated_service_time=15)
        db.session.add(q)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def authenticated_client(client):
    # Log in test user
    client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'pass123'
    })
    return client

@pytest.fixture
def staff_client(client):
    # Log in staff user
    client.post('/api/auth/login', json={
        'email': 'staff@test.com',
        'password': 'pass123'
    })
    return client

@pytest.fixture
def admin_client(client):
    # Log in admin user
    client.post('/api/auth/login', json={
        'email': 'admin@test.com',
        'password': 'pass123'
    })
    return client
