from datetime import datetime
from app.extensions import db

class Token(db.Model):
    __tablename__ = 'tokens'

    id = db.Column(db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('queues.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(15), nullable=False, default='WAITING')  # WAITING, CALLED, SERVING, COMPLETED, CANCELLED, SKIPPED, EXPIRED
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    called_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Integer, default=0, nullable=False)  # 0: Standard, 1: High, etc.
    estimated_wait_minutes = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    queue = db.relationship('Queue', back_populates='tokens')
    user = db.relationship('User', back_populates='tokens')
    notifications = db.relationship('Notification', back_populates='token', cascade='all, delete-orphan')
    events = db.relationship('QueueEvent', back_populates='token', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'queue_id': self.queue_id,
            'user_id': self.user_id,
            'token_number': self.token_number,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'called_at': self.called_at.isoformat() if self.called_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'priority': self.priority,
            'estimated_wait_minutes': self.estimated_wait_minutes
        }
        
    def formatted_token(self):
        # Generates string like Q-031 or similar (using service code prefix if available, or just a zero-padded number)
        return f"T-{self.token_number:03d}"
