"""
Flask Application Factory
Initializes and configures the Flask application with all extensions and blueprints
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name=None):
    """Application factory pattern for creating Flask app instances"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists and initialize organized structure
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize organized file structure
    with app.app_context():
        from app.utils.file_organization import ensure_uploads_structure
        ensure_uploads_structure()
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.upload import upload_bp
    from app.routes.share import share_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.website import website_bp
    from app.routes.site import site_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(share_bp, url_prefix='/r')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(website_bp, url_prefix='/website')
    app.register_blueprint(site_bp, url_prefix='/site')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {'error': 'File too large. Maximum size is 100MB'}, 413
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app

# Create app instance for direct execution
if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)