#!/usr/bin/env python
"""
Database initialization script
Creates all tables and optionally adds an admin user
"""
import os
import sys
from app import create_app, db
from app.models import User

def init_database():
    """Initialize the database with all tables"""
    # Create app with development config
    app = create_app('development')
    
    with app.app_context():
        # Drop all tables (careful in production!)
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Create admin user
        print("Creating admin user...")
        admin = User(
            email='admin@filelinkpro.com',
            full_name='Administrator',
            is_admin=True,
            is_active=True,
            storage_used=0,
            max_storage=10737418240  # 10GB
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\nAdmin account created:")
        print("  Email: admin@filelinkpro.com")
        print("  Password: admin123")
        print("\nYou can also login with:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠️  IMPORTANT: Change the admin password after first login!")

if __name__ == '__main__':
    init_database()