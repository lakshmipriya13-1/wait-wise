import pytest
from app.models.user import User
from app.extensions import db

def test_user_registration(client, app):
    # Register customer
    response = client.post('/api/auth/register', json={
        'name': 'New Customer',
        'email': 'customer@test.com',
        'phone': '1234567890',
        'password': 'password123',
        'role': 'USER'
    })
    assert response.status_code == 201
    assert response.json['success'] is True
    
    with app.app_context():
        user = User.query.filter_by(email='customer@test.com').first()
        assert user is not None
        assert user.name == 'New Customer'
        assert user.role == 'USER'

def test_user_login(client):
    response = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'pass123'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['data']['email'] == 'user@test.com'

def test_login_invalid_credentials(client):
    response = client.post('/api/auth/login', json={
        'email': 'user@test.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert response.json['success'] is False
    assert response.json['error']['code'] == 'INVALID_CREDENTIALS'
