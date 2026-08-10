-import eventlet
eventlet.monkey_patch()

import os
from app import create_app, socketio, db

app = create_app()

# Create database tables automatically when the app is initialized
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Determine host and port
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application with Socket.IO
    socketio.run(app, host=host, port=port, debug=app.debug)
