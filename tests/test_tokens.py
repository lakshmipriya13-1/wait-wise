import pytest
from app.models.token import Token
from app.models.user import User
from app.extensions import db

def test_token_creation_and_sequential_numbering(authenticated_client, app):
    # Join queue
    response = authenticated_client.post('/api/queues/1/tokens')
    assert response.status_code == 201
    assert response.json['success'] is True
    assert response.json['data']['token_number'] == 1
    
    # Try joining again - should fail as user already has an active token
    response2 = authenticated_client.post('/api/queues/1/tokens')
    assert response2.status_code == 400
    assert response2.json['success'] is False

def test_token_cancellation_and_position(client, app):
    # Create two users and generate tokens for them to test queue position updates
    with app.app_context():
        u1 = User(name="User1", email="u1@test.com")
        u1.set_password("pass123")
        u2 = User(name="User2", email="u2@test.com")
        u2.set_password("pass123")
        db.session.add_all([u1, u2])
        db.session.commit()
        
    # Login user 1 & generate token
    client.post('/api/auth/login', json={'email': 'u1@test.com', 'password': 'pass123'})
    res1 = client.post('/api/queues/1/tokens')
    t1_id = res1.json['data']['id']
    
    # Login user 2 & generate token
    client.post('/api/auth/login', json={'email': 'u2@test.com', 'password': 'pass123'})
    res2 = client.post('/api/queues/1/tokens')
    t2_id = res2.json['data']['id']
    
    # Check status for token 2 - people ahead should be 1 (user 1 is ahead)
    res_check = client.post(f'/api/tokens/{t2_id}/check')
    assert res_check.json['data']['people_ahead'] == 1
    
    # Cancel user 1's token (need to log back in as user 1 or staff)
    client.post('/api/auth/login', json={'email': 'u1@test.com', 'password': 'pass123'})
    client.post(f'/api/tokens/{t1_id}/cancel')
    
    # Check status for token 2 again - people ahead should now be 0
    res_check2 = client.post(f'/api/tokens/{t2_id}/check')
    assert res_check2.json['data']['people_ahead'] == 0
