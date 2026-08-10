import pytest
from app.models.user import User

def test_view_profile_without_auth(client):
    response = client.get('/profile')
    assert response.status_code == 302 # redirect to login

def test_view_dashboard_authenticated(authenticated_client):
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
