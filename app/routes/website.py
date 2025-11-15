"""
Website Routes Blueprint
Handles website creation, management, and publishing
"""
import os
import zipfile
import time
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, abort, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Website, WebsiteFile, File, UserFile
from app.routes.auth import login_required
from app.utils.file_organization import get_organized_file_path, ensure_uploads_structure
from datetime import datetime

website_bp = Blueprint('website', __name__)

@website_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_website():
    """Create a new website"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_public = request.form.get('is_public') == 'on'
        password = request.form.get('password')
        
        if not name:
            flash('Website name is required.', 'danger')
            return redirect(url_for('website.create_website'))
        
        # Generate slug
        slug = Website.generate_slug(name)
        
        # Create website
        website = Website(
            user_id=user.id,
            name=name,
            slug=slug,
            description=description,
            is_public=is_public,
            is_published=False
        )
        
        if password:
            website.set_password(password)
        
        db.session.add(website)
        db.session.commit()
        
        flash('Website created successfully! Now add your files.', 'success')
        return redirect(url_for('website.manage_website', website_id=website.id))
    
    return render_template('website/create.html')

@website_bp.route('/<int:website_id>/manage')
@login_required
def manage_website(website_id):
    """Manage website files and settings"""
    user = User.query.get(session['user_id'])
    website = Website.query.get_or_404(website_id)
    
    # Check ownership
    if website.user_id != user.id and not user.is_admin:
        flash('You do not have permission to manage this website.', 'danger')
        return redirect(url_for('auth.dashboard'))
    
    # Get website files
    website_files = db.session.query(WebsiteFile, File).join(
        File, WebsiteFile.file_id == File.id
    ).filter(
        WebsiteFile.website_id == website.id
    ).all()
    
    return render_template('website/manage.html', 
                         website=website, 
                         website_files=website_files,
                         user=user)  # Pass user object to template

@website_bp.route('/<int:website_id>/upload', methods=['POST'])
@login_required
def upload_website_files(website_id):
    """Upload files to a website - supports folders and automatic index detection"""
    user = User.query.get(session['user_id'])
    website = Website.query.get_or_404(website_id)
    
    # Check ownership
    if website.user_id != user.id and not user.is_admin:
        abort(403)
    
    files = request.files.getlist('files[]')
    
    if not files:
        flash('No files selected.', 'warning')
        return redirect(url_for('website.manage_website', website_id=website.id))
    
    # Check user quota for free plan (e.g., 100MB total, 50 files max)
    MAX_STORAGE_FREE = 100 * 1024 * 1024  # 100MB for free users
    MAX_FILES_FREE = 50  # 50 files max for free users
    
    # Get current usage
    current_file_count = website.website_files.count()
    
    # Check if user is on free plan (you can add a premium flag to User model)
    is_free_plan = not getattr(user, 'is_premium', False)
    
    if is_free_plan:
        if current_file_count + len(files) > MAX_FILES_FREE:
            flash(f'Free plan limit: Maximum {MAX_FILES_FREE} files per website. Upgrade to Pro for unlimited files!', 'warning')
            return redirect(url_for('website.manage_website', website_id=website.id))
        
        total_size = sum(f.content_length for f in files if f.content_length)
        if user.storage_used + total_size > MAX_STORAGE_FREE:
            remaining = MAX_STORAGE_FREE - user.storage_used
            flash(f'Free plan storage limit: {(remaining / 1024 / 1024):.1f}MB remaining. Upgrade to Pro for more storage!', 'warning')
            return redirect(url_for('website.manage_website', website_id=website.id))
    
    uploaded_count = 0
    skipped_count = 0
    index_found = False
    
    # Ensure uploads structure exists
    ensure_uploads_structure()
    
    # Get user identifier for folder organization
    user_identifier = user.username if user.username else f"user_{user.id}"
    
    # Determine common top-level folder (when uploading a directory)
    # We'll strip this folder from stored paths so that references like css/style.css resolve
    root_prefix = None
    
    # First pass to detect a consistent root prefix if present
    for f in files:
        if f and f.filename:
            norm = f.filename.replace('\\', '/')
            parts = [p for p in norm.split('/') if p]
            if len(parts) > 1:
                root_prefix = parts[0] if root_prefix is None else root_prefix
                break
    
    for file in files:
        if file and file.filename:
            # Normalize provided path (browsers may include the folder name in filename)
            original_path = file.filename.replace('\\', '/')
            parts = [p for p in original_path.split('/') if p]
            
            # Split into (folders..., base_filename)
            if len(parts) > 1:
                # Optionally strip common top-level folder
                if root_prefix and parts[0] == root_prefix:
                    parts = parts[1:]
            
            if parts:
                raw_base = parts[-1]
                raw_folders = parts[:-1]
            else:
                raw_base = original_path
                raw_folders = []
            
            # Sanitize each segment to avoid unsafe chars
            sanitized_folders = [secure_filename(seg) for seg in raw_folders if seg]
            base_filename = secure_filename(raw_base)
            
            if not base_filename:
                skipped_count += 1
                continue
            
            # Reconstruct normalized relative path (preserved folder structure)
            folder_path = '/'.join(sanitized_folders)
            full_path = f"{folder_path}/{base_filename}" if folder_path else base_filename
            
            # Generate unique stored filename (physical storage name)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            random_str = secrets.token_hex(8)
            ext = ''
            if '.' in base_filename:
                ext = '.' + base_filename.rsplit('.', 1)[1].lower()
            stored_filename = f"{timestamp}_{random_str}{ext}"
            
            # Save file to organized folder structure (websitefiles)
            file_path = get_organized_file_path('websitefiles', user_identifier, stored_filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Skip files over 50MB (reasonable limit per file)
            if file_size > 50 * 1024 * 1024:
                os.remove(file_path)
                flash(f'File {base_filename} is too large (max 50MB per file)', 'warning')
                skipped_count += 1
                continue
            
            # Create file record
            new_file = File(
                original_filename=base_filename,  # Store just the filename
                stored_filename=stored_filename,
                file_size=file_size,
                mime_type=file.content_type or 'application/octet-stream',
                upload_ip=request.remote_addr
            )
            db.session.add(new_file)
            db.session.flush()
            
            # Create user file association
            user_file = UserFile(
                user_id=user.id,
                file_id=new_file.id
            )
            db.session.add(user_file)
            
            # Automatic index.html detection - check various locations
            is_index_file = False
            filename_lower = base_filename.lower()
            
            # Check if it's index.html - PRIMARY CHECK
            if filename_lower in ['index.html', 'index.htm']:
                # If there's no existing index file, make this one the index
                existing_index = website.website_files.filter_by(is_index=True).first()
                if not existing_index:
                    is_index_file = True
                    index_found = True
                # If at root level (no folder), always prefer this as index
                elif not folder_path:
                    # Unmark the old index
                    if existing_index:
                        existing_index.is_index = False
                    is_index_file = True
                    index_found = True
            
            # Also accept other common homepage files if no index.html exists
            if not is_index_file and not index_found:
                other_patterns = ['default.html', 'default.htm', 'home.html', 'home.htm']
                if filename_lower in other_patterns:
                    existing_index = website.website_files.filter_by(is_index=True).first()
                    if not existing_index:
                        is_index_file = True
                        index_found = True
            
            # Create website file association with normalized folder path
            website_file = WebsiteFile(
                website_id=website.id,
                file_id=new_file.id,
                file_path=full_path,  # Store full path relative to root
                is_index=is_index_file
            )
            db.session.add(website_file)
            
            # Update user storage
            user.update_storage(file_size)
            
            uploaded_count += 1
    
    db.session.commit()
    
    # Provide feedback
    if uploaded_count > 0:
        flash(f'✅ {uploaded_count} file(s) uploaded successfully!', 'success')
        if index_found:
            flash('🎉 Index file detected! Your website is ready to publish.', 'success')
        elif not website.website_files.filter_by(is_index=True).first():
            flash('💡 Tip: Upload an index.html file to publish your website.', 'info')
    
    if skipped_count > 0:
        flash(f'⚠️ {skipped_count} file(s) were skipped due to issues.', 'warning')
    
    return redirect(url_for('website.manage_website', website_id=website.id))

@website_bp.route('/<int:website_id>/publish', methods=['POST'])
@login_required
def publish_website(website_id):
    """Publish or unpublish a website"""
    
    user = User.query.get(session['user_id'])
    website = Website.query.get_or_404(website_id)
    
    # Check ownership
    if website.user_id != user.id and not user.is_admin:
        abort(403)
    
    # Check if website has files
    if website.website_files.count() == 0:
        flash('Please upload files before publishing.', 'warning')
        return redirect(url_for('website.manage_website', website_id=website.id))
    
    # Check if website has index file
    has_index = website.website_files.filter_by(is_index=True).first() is not None
    if not has_index:
        flash('Please upload an index.html file to publish your website.', 'warning')
        return redirect(url_for('website.manage_website', website_id=website.id))
    
    # Publishing status will be toggled immediately for better performance
    
    # Toggle publish status
    website.is_published = not website.is_published
    website.updated_date = datetime.utcnow()
    db.session.commit()
    
    if website.is_published:
        flash(f'✨ Website published successfully! Your website is now live at /site/{website.slug}', 'success')
    else:
        flash('Website unpublished successfully.', 'info')
    
    return redirect(url_for('website.manage_website', website_id=website.id))

@website_bp.route('/<int:website_id>/delete', methods=['POST'])
@login_required
def delete_website(website_id):
    """Delete a website and all associated files"""
    user = User.query.get(session['user_id'])
    website = Website.query.get_or_404(website_id)
    
    # Check ownership
    if website.user_id != user.id and not user.is_admin:
        abort(403)
    
    # Delete website (cascade will delete website_files)
    db.session.delete(website)
    db.session.commit()
    
    flash('Website deleted successfully.', 'info')
    return redirect(url_for('auth.dashboard'))

@website_bp.route('/my-websites')
@login_required
def my_websites():
    """List all user's websites"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    websites = Website.query.filter_by(user_id=user.id).order_by(Website.updated_date.desc()).all()
    
    return render_template('website/my_websites.html', websites=websites)

@website_bp.route('/<int:website_id>/fix-index', methods=['POST'])
@login_required
def fix_index_detection(website_id):
    """Re-scan website files and fix index.html detection"""
    user = User.query.get(session['user_id'])
    website = Website.query.get_or_404(website_id)
    
    # Check ownership
    if website.user_id != user.id and not user.is_admin:
        abort(403)
    
    # First, unmark all existing index files for this website
    WebsiteFile.query.filter_by(website_id=website.id).update({'is_index': False})
    
    # Then, scan all files to find the best candidate for index
    index_found = False
    root_index = None
    other_indexes = []

    # Query all files at once to minimize DB calls
    all_website_files = db.session.query(WebsiteFile, File).join(File, WebsiteFile.file_id == File.id).filter(WebsiteFile.website_id == website.id).all()

    for wf, file in all_website_files:
        filename_lower = file.original_filename.lower()
        
        if filename_lower in ['index.html', 'index.htm']:
            file_path = wf.file_path or ''
            is_root = not '/' in file_path or file_path == file.original_filename

            if is_root:
                if not root_index: # Find the first root index
                    root_index = wf
            else:
                other_indexes.append(wf)

    # Prioritize root index, then other indexes
    if root_index:
        root_index.is_index = True
        index_found = True
    elif other_indexes:
        other_indexes[0].is_index = True # Mark the first one found
        index_found = True

    # If still no index.html, check for other common files like home.html at root
    if not index_found:
        for wf, file in all_website_files:
            filename_lower = file.original_filename.lower()
            if filename_lower in ['default.html', 'default.htm', 'home.html', 'home.htm']:
                file_path = wf.file_path or ''
                is_root = not '/' in file_path or file_path == file.original_filename
                if is_root:
                    wf.is_index = True
                    index_found = True
                    break
    
    db.session.commit()
    
    if index_found:
        flash('✅ Index file detected successfully! Your website is ready to publish.', 'success')
    else:
        flash('⚠️ No index.html file found. Please upload an index.html file.', 'warning')
    
    return redirect(url_for('website.manage_website', website_id=website.id))

@website_bp.route('/<int:website_id>/cleanup-duplicates', methods=['POST'])
@login_required
def cleanup_duplicate_files(website_id):
    """Remove duplicate files from website"""
    user = User.query.get(session['user_id'])
    website = Website.query.get_or_404(website_id)
    
    # Check ownership
    if website.user_id != user.id and not user.is_admin:
        abort(403)
    
    # Get all website files
    website_files = list(website.website_files)
    seen_files = {}
    duplicates_removed = 0
    
    # Group files by filename and path
    for wf in website_files:
        file = wf.file
        key = (file.original_filename.lower(), wf.file_path or '')
        
        if key in seen_files:
            # This is a duplicate - keep the newer one (higher ID)
            existing_wf = seen_files[key]
            if wf.id > existing_wf.id:
                # Remove the older one
                db.session.delete(existing_wf)
                seen_files[key] = wf
            else:
                # Remove this one
                db.session.delete(wf)
            duplicates_removed += 1
        else:
            seen_files[key] = wf
    
    db.session.commit()
    
    if duplicates_removed > 0:
        flash(f'✅ Removed {duplicates_removed} duplicate file(s).', 'success')
        
        # Re-run index detection after cleanup
        return redirect(url_for('website.fix_index_detection', website_id=website.id))
    else:
        flash('ℹ️ No duplicate files found.', 'info')
        return redirect(url_for('website.manage_website', website_id=website.id))
