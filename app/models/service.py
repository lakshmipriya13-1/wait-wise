from datetime import datetime
from app.extensions import db

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    average_service_time = db.Column(db.Integer, default=15, nullable=False)  # in minutes
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = db.relationship('Organization', back_populates='services')
    queues = db.relationship('Queue', back_populates='service', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'name': self.name,
            'description': self.description,
            'average_service_time': self.average_service_time,
            'active': self.active,
            'created_at': self.created_at.isoformat()
        }
