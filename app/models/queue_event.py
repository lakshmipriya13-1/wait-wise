from datetime import datetime
from app.extensions import db

class QueueEvent(db.Model):
    __tablename__ = 'queue_events'

    id = db.Column(db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('queues.id'), nullable=False)
    token_id = db.Column(db.Integer, db.ForeignKey('tokens.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # TOKEN_CREATED, TOKEN_CALLED, etc.
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)  # Using metadata_json to avoid SQLAlchemy namespace conflicts with metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    queue = db.relationship('Queue', back_populates='events')
    token = db.relationship('Token', back_populates='events')

    def to_dict(self):
        return {
            'id': self.id,
            'queue_id': self.queue_id,
            'token_id': self.token_id,
            'event_type': self.event_type,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'metadata': self.metadata_json,
            'created_at': self.created_at.isoformat()
        }
