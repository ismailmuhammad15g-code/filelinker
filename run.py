#!/usr/bin/env python
"""
Development server runner
Run the Flask application in development mode
"""
import os
from app import create_app

if __name__ == '__main__':
    # Get environment from ENV variable or default to development
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Create the Flask app
    app = create_app(env)
    
    # Run the development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(env == 'development')
    )