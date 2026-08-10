from flask import request
from flask_socketio import join_room, leave_room
from app.extensions import socketio
from app.utils.logger import logger

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_queue')
def handle_join_queue(data):
    """
    Subscribes client to a specific queue's updates.
    """
    queue_id = data.get('queue_id')
    if queue_id:
        room = f"queue_{queue_id}"
        join_room(room)
        logger.info(f"Client {request.sid} joined room: {room}")

@socketio.on('leave_queue')
def handle_leave_queue(data):
    """
    Unsubscribes client from a specific queue's updates.
    """
    queue_id = data.get('queue_id')
    if queue_id:
        room = f"queue_{queue_id}"
        leave_room(room)
        logger.info(f"Client {request.sid} left room: {room}")

@socketio.on('join_user')
def handle_join_user(data):
    """
    Subscribes a logged-in user to their personal notification channel.
    """
    user_id = data.get('user_id')
    if user_id:
        room = f"user_{user_id}"
        join_room(room)
        logger.info(f"User {user_id} (Client {request.sid}) joined personal room: {room}")

@socketio.on('leave_user')
def handle_leave_user(data):
    """
    Unsubscribes a logged-in user from their personal notification channel.
    """
    user_id = data.get('user_id')
    if user_id:
        room = f"user_{user_id}"
        leave_room(room)
        logger.info(f"User {user_id} (Client {request.sid}) left personal room: {room}")
