import pytest
from app.models.queue import Queue
from app.extensions import db

def test_get_queues_list(client):
    response = client.get('/api/queues')
    assert response.status_code == 200
    assert response.json['success'] is True
    assert len(response.json['data']) == 1
    assert response.json['data'][0]['name'] == 'Test Queue'

def test_queue_pause_resume(staff_client, app):
    # Pause queue
    response = staff_client.post('/api/admin/queues/1/pause')
    assert response.status_code == 200
    assert response.json['success'] is True
    
    with app.app_context():
        q = Queue.query.get(1)
        assert q.status == 'PAUSED'
        
    # Resume queue
    response = staff_client.post('/api/admin/queues/1/resume')
    assert response.status_code == 200
    assert response.json['success'] is True
    
    with app.app_context():
        q = Queue.query.get(1)
        assert q.status == 'OPEN'
