"""
Flask Application Configuration
Handles environment-specific configuration for the file sharing platform
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class with default settings"""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    
    # File Upload Settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = set()  # Empty set means all extensions allowed
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filelink.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Link Settings
    LINK_EXPIRY_DAYS = 0  # 0 means links never expire
    ENABLE_ANALYTICS = True
    ENABLE_PASSWORD_PROTECTION = True
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Application Settings
    APP_NAME = "FileLink Pro"
    APP_DESCRIPTION = "Professional File Sharing Platform"
    APP_VERSION = "1.0.0"

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    ENV = 'development'

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}