import pytest
from app.models.queue import Queue
from app.models.token import Token
from app.extensions import db

def test_admin_call_next_unauthorized(client):
    # Try calling next without being staff/admin
    response = client.post('/api/admin/queues/1/next')
    assert response.status_code == 401 # unauthorized

def test_admin_call_next_and_complete_actions(staff_client, app):
    # First join queue as standard user
    with app.app_context():
        # Add a token manually to test
        t = Token(queue_id=1, user_id=3, token_number=1, status='WAITING')
        db.session.add(t)
        db.session.commit()
        
    # Call next
    response = staff_client.post('/api/admin/queues/1/next')
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['data']['status'] == 'CALLED'
    
    # Complete token
    response2 = staff_client.post('/api/admin/tokens/1/complete')
    assert response2.status_code == 200
    assert response2.json['success'] is True
    assert response2.json['data']['status'] == 'COMPLETED'
