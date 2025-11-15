#!/usr/bin/env python
"""
Production server runner using Waitress (Windows-compatible)
"""
import os
from waitress import serve
from app import create_app

if __name__ == '__main__':
    # Get environment from ENV variable or default to production
    env = os.environ.get('FLASK_ENV', 'production')
    
    # Create the Flask app
    app = create_app(env)
    
    # Configure Waitress
    host = '0.0.0.0'
    port = 5000
    
    print(f"Starting Waitress server on http://{host}:{port}")
    print(f"Environment: {env}")
    print("Press Ctrl+C to quit")
    
    # Serve with Waitress (production-ready server for Windows)
    serve(app, host=host, port=port, threads=4)