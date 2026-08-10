from datetime import datetime
from app.extensions import db

class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    organization_type = db.Column(db.String(50), nullable=False)  # Hospital, Bank, Service Center, etc.
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    services = db.relationship('Service', back_populates='organization', cascade='all, delete-orphan')
    queues = db.relationship('Queue', back_populates='organization', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'organization_type': self.organization_type,
            'address': self.address,
            'created_at': self.created_at.isoformat()
        }
