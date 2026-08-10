from datetime import datetime
from app.extensions import db

class Queue(db.Model):
    __tablename__ = 'queues'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(15), nullable=False, default='OPEN')  # OPEN, PAUSED, CLOSED
    current_token_number = db.Column(db.Integer, default=0, nullable=False) # currently being served token number
    estimated_service_time = db.Column(db.Integer, default=15, nullable=False) # in minutes, average per person
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = db.relationship('Organization', back_populates='queues')
    service = db.relationship('Service', back_populates='queues')
    tokens = db.relationship('Token', back_populates='queue', cascade='all, delete-orphan')
    events = db.relationship('QueueEvent', back_populates='queue', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'service_id': self.service_id,
            'name': self.name,
            'status': self.status,
            'current_token_number': self.current_token_number,
            'estimated_service_time': self.estimated_service_time,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
