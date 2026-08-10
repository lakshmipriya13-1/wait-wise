import sys
import os
from datetime import datetime, timedelta

# Ensure waitwise root directory is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.organization import Organization
from app.models.service import Service
from app.models.queue import Queue
from app.models.token import Token
from app.models.queue_event import QueueEvent

def seed_database():
    print("Initializing Database Seeding...")
    app = create_app('development')
    
    with app.app_context():
        # Clean existing tables
        print("Dropping existing tables...")
        db.drop_all()
        print("Recreating database tables...")
        db.create_all()
        
        # Create users
        print("Creating default seed users...")
        
        admin_user = User(
            name="System Admin (Demo)",
            email="admin@waitwise.com",
            phone="1234567890",
            role="ADMIN",
            is_active=True
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        
        staff_user = User(
            name="General Desk Staff (Demo)",
            email="staff@waitwise.com",
            phone="1234567891",
            role="STAFF",
            is_active=True
        )
        staff_user.set_password("staff123")
        db.session.add(staff_user)
        
        users_list = []
        for i in range(1, 11):
            u = User(
                name=f"Demo Customer {i}",
                email=f"user{i}@waitwise.com",
                phone=f"123456780{i}",
                role="USER",
                is_active=True
            )
            u.set_password("user123")
            db.session.add(u)
            users_list.append(u)
            
        # Create organizations
        print("Creating demo organizations...")
        hospital = Organization(
            name="City Health General Hospital",
            organization_type="Hospital",
            address="100 Medical Center Way, Metro City"
        )
        db.session.add(hospital)
        
        bank = Organization(
            name="First Metro Bank",
            organization_type="Bank",
            address="500 Financial Plaza, Downtown"
        )
        db.session.add(bank)
        db.session.commit() # Save to get IDs
        
        # Create services
        print("Creating organization services...")
        consultation = Service(
            organization_id=hospital.id,
            name="General Consultation",
            description="Regular outpatient checks, health advice and doctor reviews.",
            average_service_time=15,
            active=True
        )
        db.session.add(consultation)
        
        cardiology = Service(
            organization_id=hospital.id,
            name="Cardiology Center",
            description="Heart rate checks, ECG reviews, cardiac consultations.",
            average_service_time=20,
            active=True
        )
        db.session.add(cardiology)
        
        billing = Service(
            organization_id=bank.id,
            name="Accounts & Billing",
            description="Open accounts, resolve card issues, manage loans.",
            average_service_time=10,
            active=True
        )
        db.session.add(billing)
        db.session.commit()
        
        # Create queues
        print("Creating queues counters...")
        consultation_q = Queue(
            organization_id=hospital.id,
            service_id=consultation.id,
            name="Doctor Consultation Queue A",
            status="OPEN",
            current_token_number=2, # Currently serving token number 2
            estimated_service_time=15
        )
        db.session.add(consultation_q)
        
        cardiology_q = Queue(
            organization_id=hospital.id,
            service_id=cardiology.id,
            name="Cardiology Queue 1",
            status="OPEN",
            current_token_number=0,
            estimated_service_time=20
        )
        db.session.add(cardiology_q)
        
        billing_q = Queue(
            organization_id=bank.id,
            service_id=billing.id,
            name="Billing Counter 3",
            status="OPEN",
            current_token_number=1,
            estimated_service_time=10
        )
        db.session.add(billing_q)
        db.session.commit()
        
        # Create sample tokens
        print("Creating sample tokens...")
        
        # Consultation Q tokens
        # Token 1: Completed
        t1 = Token(
            queue_id=consultation_q.id,
            user_id=users_list[0].id,
            token_number=1,
            status="COMPLETED",
            created_at=datetime.utcnow() - timedelta(hours=2),
            called_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            estimated_wait_minutes=0
        )
        db.session.add(t1)
        
        # Token 2: Called/Serving
        t2 = Token(
            queue_id=consultation_q.id,
            user_id=users_list[1].id,
            token_number=2,
            status="CALLED",
            created_at=datetime.utcnow() - timedelta(hours=1),
            called_at=datetime.utcnow() - timedelta(minutes=15),
            estimated_wait_minutes=0
        )
        db.session.add(t2)
        
        # Token 3: Waiting
        t3 = Token(
            queue_id=consultation_q.id,
            user_id=users_list[2].id,
            token_number=3,
            status="WAITING",
            created_at=datetime.utcnow() - timedelta(minutes=30),
            estimated_wait_minutes=15
        )
        db.session.add(t3)
        
        # Token 4: Waiting
        t4 = Token(
            queue_id=consultation_q.id,
            user_id=users_list[3].id,
            token_number=4,
            status="WAITING",
            created_at=datetime.utcnow() - timedelta(minutes=10),
            estimated_wait_minutes=30
        )
        db.session.add(t4)
        
        # Token 5: Cancelled
        t5 = Token(
            queue_id=consultation_q.id,
            user_id=users_list[4].id,
            token_number=5,
            status="CANCELLED",
            created_at=datetime.utcnow() - timedelta(minutes=5),
            cancelled_at=datetime.utcnow() - timedelta(minutes=1),
            estimated_wait_minutes=0
        )
        db.session.add(t5)
        
        # Billing Q tokens
        # Token 1: Serving
        t6 = Token(
            queue_id=billing_q.id,
            user_id=users_list[5].id,
            token_number=1,
            status="SERVING",
            created_at=datetime.utcnow() - timedelta(minutes=25),
            called_at=datetime.utcnow() - timedelta(minutes=5),
            estimated_wait_minutes=0
        )
        db.session.add(t6)
        
        # Token 2: Waiting
        t7 = Token(
            queue_id=billing_q.id,
            user_id=users_list[6].id,
            token_number=2,
            status="WAITING",
            created_at=datetime.utcnow() - timedelta(minutes=5),
            estimated_wait_minutes=10
        )
        db.session.add(t7)
        db.session.commit()
        
        # Create events history
        print("Creating queue events logs...")
        events = [
            QueueEvent(queue_id=consultation_q.id, token_id=t1.id, event_type="TOKEN_CREATED", new_status="WAITING", created_at=datetime.utcnow() - timedelta(hours=2)),
            QueueEvent(queue_id=consultation_q.id, token_id=t1.id, event_type="TOKEN_CALLED", old_status="WAITING", new_status="CALLED", created_at=datetime.utcnow() - timedelta(hours=1, minutes=45)),
            QueueEvent(queue_id=consultation_q.id, token_id=t1.id, event_type="TOKEN_COMPLETED", old_status="CALLED", new_status="COMPLETED", created_at=datetime.utcnow() - timedelta(hours=1, minutes=30)),
            
            QueueEvent(queue_id=consultation_q.id, token_id=t2.id, event_type="TOKEN_CREATED", new_status="WAITING", created_at=datetime.utcnow() - timedelta(hours=1)),
            QueueEvent(queue_id=consultation_q.id, token_id=t2.id, event_type="TOKEN_CALLED", old_status="WAITING", new_status="CALLED", created_at=datetime.utcnow() - timedelta(minutes=15)),
            
            QueueEvent(queue_id=consultation_q.id, token_id=t3.id, event_type="TOKEN_CREATED", new_status="WAITING", created_at=datetime.utcnow() - timedelta(minutes=30)),
            QueueEvent(queue_id=consultation_q.id, token_id=t4.id, event_type="TOKEN_CREATED", new_status="WAITING", created_at=datetime.utcnow() - timedelta(minutes=10)),
            
            QueueEvent(queue_id=consultation_q.id, token_id=t5.id, event_type="TOKEN_CREATED", new_status="WAITING", created_at=datetime.utcnow() - timedelta(minutes=5)),
            QueueEvent(queue_id=consultation_q.id, token_id=t5.id, event_type="TOKEN_CANCELLED", old_status="WAITING", new_status="CANCELLED", created_at=datetime.utcnow() - timedelta(minutes=1)),
        ]
        db.session.bulk_save_objects(events)
        db.session.commit()
        
        print("\nDatabase Seeding successfully completed.")
        print("-" * 50)
        print("DEMO CREDENTIALS:")
        print("Admin User:")
        print("  Email:    admin@waitwise.com")
        print("  Password: admin123")
        print("Staff User:")
        print("  Email:    staff@waitwise.com")
        print("  Password: staff123")
        print("Standard Customer (1 to 10):")
        print("  Email:    user1@waitwise.com to user10@waitwise.com")
        print("  Password: user123")
        print("-" * 50)

if __name__ == '__main__':
    seed_database()
