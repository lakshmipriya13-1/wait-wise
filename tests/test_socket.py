import pytest
from app import socketio

def test_socket_connection(app):
    # Set up flask socket test client
    flask_test_client = app.test_client()
    socket_client = socketio.test_client(app, flask_test_client=flask_test_client)
    
    assert socket_client.is_connected()
    
    # Test joining a queue room
    socket_client.emit('join_queue', {'queue_id': 1})
    
    # Disconnect
    socket_client.disconnect()
