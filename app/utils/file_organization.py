"""
File Organization Utilities
Handles organized file storage for shared files and website files
"""
import os
from flask import current_app

def get_user_identifier(session=None, default_user="anonymous"):
    """Get user identifier for folder naming"""
    if session and 'username' in session:
        return session['username']
    elif session and 'user_id' in session:
        # If we have user_id but no username, we could fetch from database
        from app.models import User
        user = User.query.get(session['user_id'])
        if user:
            return user.username
    return default_user

def create_user_folder(folder_type, user_identifier):
    """Create user-specific folder if it doesn't exist"""
    base_path = current_app.config['UPLOAD_FOLDER']
    user_folder = os.path.join(base_path, folder_type, user_identifier)
    
    if not os.path.exists(user_folder):
        os.makedirs(user_folder, exist_ok=True)
    
    return user_folder

def get_organized_file_path(folder_type, user_identifier, filename):
    """Get the organized file path for storage"""
    user_folder = create_user_folder(folder_type, user_identifier)
    return os.path.join(user_folder, filename)

def get_relative_organized_path(folder_type, user_identifier, filename):
    """Get relative path for database storage"""
    return os.path.join(folder_type, user_identifier, filename)

def ensure_uploads_structure():
    """Ensure the uploads folder has the correct structure"""
    base_path = current_app.config['UPLOAD_FOLDER']
    
    # Create main folders
    folders = ['sharedfiles', 'websitefiles']
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

def find_file_in_organized_structure(filename):
    """Find a file in the organized structure (for legacy support)"""
    base_path = current_app.config['UPLOAD_FOLDER']
    
    # Check flat structure first (for old files)
    flat_path = os.path.join(base_path, filename)
    if os.path.exists(flat_path):
        return flat_path
    
    # Check organized structure
    for folder_type in ['sharedfiles', 'websitefiles']:
        folder_path = os.path.join(base_path, folder_type)
        if os.path.exists(folder_path):
            for user_folder in os.listdir(folder_path):
                user_path = os.path.join(folder_path, user_folder)
                if os.path.isdir(user_path):
                    file_path = os.path.join(user_path, filename)
                    if os.path.exists(file_path):
                        return file_path
    
    return None