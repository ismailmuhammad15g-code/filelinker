#!/usr/bin/env python
"""
WSGI entry point for production deployment with Gunicorn
"""
import os
from app import create_app

# Get environment from ENV variable or default to production
env = os.environ.get('FLASK_ENV', 'production')

# Create the Flask app instance
app = create_app(env)

if __name__ == '__main__':
    app.run()
