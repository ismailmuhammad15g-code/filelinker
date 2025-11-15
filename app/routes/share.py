"""
Share Routes Blueprint
Handles file sharing, downloading, and preview functionality
"""
import os
from flask import Blueprint, render_template, request, send_file, abort, current_app, jsonify
from app import db
from app.models import Link, File, Analytics
from app.utils.file_organization import find_file_in_organized_structure

share_bp = Blueprint('share', __name__)

@share_bp.route('/<slug>', methods=['GET', 'POST'])
def share_link(slug):
    """Handle shared link access"""
    # Find the link
    link = Link.query.filter_by(slug=slug, is_active=True).first()
    
    if not link:
        abort(404)
    
    # Check if link is expired
    if link.is_expired():
        return render_template('expired.html'), 410
    
    # Check if password protected
    if link.password_hash:
        # Check if password was submitted via POST or GET
        password = request.form.get('password') or request.args.get('password')
        if not password or not link.check_password(password):
            if request.method == 'POST':
                from flask import flash
                flash('Invalid password', 'danger')
            return render_template('password_protect.html', slug=slug)
        
        # If password is correct, redirect to include password in URL for links to work
        if request.method == 'POST':
            from flask import redirect, url_for
            return redirect(url_for('share.share_link', slug=slug, password=password))
    
    # Get the associated file
    file = link.file
    if not file:
        abort(404)
    
    # Track analytics
    if current_app.config['ENABLE_ANALYTICS']:
        analytics = Analytics(
            link_id=link.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            referrer=request.headers.get('Referer', '')
        )
        db.session.add(analytics)
        link.increment_views()
    
    # Check if file is previewable
    if file.is_previewable():
        preview_type = file.get_preview_type()
        return render_template('share_page.html', link=link, file=file, preview=True, preview_type=preview_type)
    else:
        return render_template('share_page.html', link=link, file=file, preview=False, preview_type=None)

@share_bp.route('/<slug>/download')
def download_file(slug):
    """Direct file download"""
    # Find the link
    link = Link.query.filter_by(slug=slug, is_active=True).first()
    
    if not link:
        abort(404)
    
    # Check if link is expired
    if link.is_expired():
        abort(410)
    
    # Check password if protected
    if link.password_hash:
        password = request.args.get('password')
        if not password or not link.check_password(password):
            abort(403)
    
    # Get the file
    file = link.file
    if not file:
        abort(404)
    
    # Get file path - check organized structure first
    file_path = find_file_in_organized_structure(file.stored_filename)
    
    if not file_path or not os.path.exists(file_path):
        abort(404)
    
    # Track download in analytics
    if current_app.config['ENABLE_ANALYTICS']:
        analytics = Analytics(
            link_id=link.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            referrer=request.headers.get('Referer', '')
        )
        db.session.add(analytics)
        link.increment_views()
    
    # Send file
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.original_filename,
        mimetype=file.mime_type
    )

@share_bp.route('/<slug>/preview')
def preview_file(slug):
    """Enhanced file preview for multiple file types"""
    from flask import Response
    import mimetypes
    
    # Find the link
    link = Link.query.filter_by(slug=slug, is_active=True).first()
    
    if not link:
        abort(404)
    
    # Check if link is expired
    if link.is_expired():
        abort(410)
    
    # Check password if protected
    if link.password_hash:
        password = request.args.get('password')
        if not password or not link.check_password(password):
            abort(403)
    
    # Get the file
    file = link.file
    if not file or not file.is_previewable():
        abort(404)
    
    # Get file path - check organized structure first
    file_path = find_file_in_organized_structure(file.stored_filename)
    
    if not file_path or not os.path.exists(file_path):
        abort(404)
    
    # Track preview in analytics
    if current_app.config['ENABLE_ANALYTICS']:
        link.increment_views()
    
    # Get preview type
    preview_type = file.get_preview_type()
    ext = file.get_file_extension()
    
    # Handle different file types
    if preview_type == 'image':
        # Serve image files directly
        return send_file(file_path, mimetype=file.mime_type)
    
    elif preview_type == 'pdf':
        # Serve PDF files directly
        return send_file(file_path, mimetype='application/pdf')
    
    elif preview_type in ['audio', 'video']:
        # Serve media files directly
        mime_type = mimetypes.guess_type(file_path)[0] or file.mime_type
        return send_file(file_path, mimetype=mime_type)
    
    elif preview_type in ['text', 'html']:
        # Handle text-based files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except:
                abort(500)
        except:
            abort(500)
        
        if ext in ['html', 'htm']:
            return content, 200, {'Content-Type': 'text/plain'}
        elif ext == 'css':
            return content, 200, {'Content-Type': 'text/css'}
        elif ext == 'js':
            return content, 200, {'Content-Type': 'application/javascript'}
        elif ext == 'json':
            return content, 200, {'Content-Type': 'application/json'}
        elif ext == 'xml':
            return content, 200, {'Content-Type': 'text/xml'}
        else:
            return content, 200, {'Content-Type': 'text/plain'}
    
    else:
        abort(404)

@share_bp.route('/<slug>/info')
def link_info(slug):
    """Get link information (API endpoint)"""
    # Find the link
    link = Link.query.filter_by(slug=slug, is_active=True).first()
    
    if not link:
        return jsonify({'error': 'Link not found'}), 404
    
    # Get file info
    file = link.file
    
    return jsonify({
        'slug': link.slug,
        'file': {
            'name': file.original_filename,
            'size': file.file_size,
            'type': file.mime_type,
            'uploaded': file.upload_date.isoformat()
        },
        'link': {
            'created': link.created_date.isoformat(),
            'views': link.view_count,
            'last_accessed': link.last_accessed.isoformat() if link.last_accessed else None,
            'expires': link.expiry_date.isoformat() if link.expiry_date else None,
            'password_protected': bool(link.password_hash)
        }
    })

@share_bp.route('/<slug>/verify-password', methods=['POST'])
def verify_password(slug):
    """Verify password for protected link"""
    # Find the link
    link = Link.query.filter_by(slug=slug, is_active=True).first()
    
    if not link:
        return jsonify({'error': 'Link not found'}), 404
    
    if not link.password_hash:
        return jsonify({'error': 'Link is not password protected'}), 400
    
    password = request.json.get('password')
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    if link.check_password(password):
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Invalid password'}), 403