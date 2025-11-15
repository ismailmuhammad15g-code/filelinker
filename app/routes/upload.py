"""
Upload Routes Blueprint
Handles file upload functionality and link generation
"""
import os
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from app import db, limiter
from app.models import File, Link, User, UserFile
from app.utils.file_organization import get_user_identifier, get_organized_file_path, ensure_uploads_structure

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    """Check if file extension is allowed (all files allowed by default)"""
    return True  # Accept all file types

def generate_unique_filename(original_filename):
    """Generate a unique filename for storage"""
    ext = ''
    if '.' in original_filename:
        ext = '.' + original_filename.rsplit('.', 1)[1].lower()
    
    # Generate unique filename with timestamp and random string
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    random_str = secrets.token_hex(8)
    return f"{timestamp}_{random_str}{ext}"

@upload_bp.route('/')
def upload_page():
    """Display the upload page"""
    return render_template('upload.html')

@upload_bp.route('/process', methods=['POST'])
@limiter.limit("10 per minute")
def process_upload():
    """Process file upload and generate shareable link"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if file and allowed_file(file.filename):
            # Ensure uploads structure exists
            ensure_uploads_structure()
            
            # Get user identifier for folder organization
            user_identifier = get_user_identifier(session)
            
            # Secure the filename
            original_filename = secure_filename(file.filename)
            if not original_filename:
                original_filename = 'unnamed_file'
            
            # Generate unique stored filename
            stored_filename = generate_unique_filename(original_filename)
            
            # Save file to organized folder structure (sharedfiles)
            file_path = get_organized_file_path('sharedfiles', user_identifier, stored_filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Determine MIME type
            mime_type = file.content_type or 'application/octet-stream'
            
            # Create database record for file
            new_file = File(
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                mime_type=mime_type,
                upload_ip=request.remote_addr
            )
            db.session.add(new_file)
            db.session.flush()  # Get the file ID
            
            # Generate shareable link
            slug = Link.generate_slug()
            
            # Handle optional parameters
            password = request.form.get('password', '')
            expiry_days = request.form.get('expiry_days', type=int)
            
            # Create link record
            new_link = Link(
                slug=slug,
                file_id=new_file.id
            )
            
            # Set password if provided
            if password:
                new_link.set_password(password)
            
            # Set expiry if provided
            if expiry_days and expiry_days > 0:
                new_link.expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
            
            db.session.add(new_link)
            
            # Create user-file association if user is logged in
            if 'user_id' in session:
                user_file = UserFile(
                    user_id=session['user_id'],
                    file_id=new_file.id
                )
                db.session.add(user_file)
                
                # Update user storage usage
                user = User.query.get(session['user_id'])
                if user:
                    user.update_storage(file_size)
            
            db.session.commit()
            
            # Generate full URL
            base_url = request.url_root.rstrip('/')
            full_url = new_link.get_full_url(base_url)
            
            # Return success response
            return jsonify({
                'success': True,
                'file': {
                    'name': original_filename,
                    'size': file_size,
                    'type': mime_type
                },
                'link': {
                    'url': full_url,
                    'slug': slug,
                    'password_protected': bool(password),
                    'expiry_date': new_link.expiry_date.isoformat() if new_link.expiry_date else None
                }
            }), 200
            
        else:
            return jsonify({'error': 'File type not allowed'}), 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Upload failed. Please try again.'}), 500

@upload_bp.route('/bulk', methods=['POST'])
@limiter.limit("5 per minute")
def bulk_upload():
    """Handle multiple file uploads"""
    try:
        files = request.files.getlist('files[]')
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        # Ensure uploads structure exists
        ensure_uploads_structure()
        
        # Get user identifier for folder organization
        user_identifier = get_user_identifier(session)
        
        results = []
        base_url = request.url_root.rstrip('/')
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                # Process each file
                original_filename = secure_filename(file.filename) or 'unnamed_file'
                stored_filename = generate_unique_filename(original_filename)
                
                # Save file to organized folder structure (sharedfiles)
                file_path = get_organized_file_path('sharedfiles', user_identifier, stored_filename)
                file.save(file_path)
                
                # Create database records
                new_file = File(
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_size=os.path.getsize(file_path),
                    mime_type=file.content_type or 'application/octet-stream',
                    upload_ip=request.remote_addr
                )
                db.session.add(new_file)
                db.session.flush()
                
                # Create link
                slug = Link.generate_slug()
                new_link = Link(slug=slug, file_id=new_file.id)
                db.session.add(new_link)
                
                # Create user-file association if user is logged in
                if 'user_id' in session:
                    user_file = UserFile(
                        user_id=session['user_id'],
                        file_id=new_file.id
                    )
                    db.session.add(user_file)
                    
                    # Update user storage usage
                    user = User.query.get(session['user_id'])
                    if user:
                        user.update_storage(new_file.file_size)
                
                results.append({
                    'filename': original_filename,
                    'url': new_link.get_full_url(base_url),
                    'slug': slug
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'files': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk upload error: {str(e)}")
        return jsonify({'error': 'Bulk upload failed'}), 500