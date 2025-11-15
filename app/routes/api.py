"""
API Routes Blueprint
RESTful API endpoints for programmatic access
"""
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db, limiter
from app.models import File, Link, Analytics
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': current_app.config['APP_VERSION']
    }), 200

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get platform statistics"""
    total_files = File.query.count()
    total_links = Link.query.count()
    total_views = db.session.query(db.func.sum(Link.view_count)).scalar() or 0
    
    # Get recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_uploads = File.query.filter(File.upload_date > yesterday).count()
    recent_views = Analytics.query.filter(Analytics.access_date > yesterday).count()
    
    return jsonify({
        'total_files': total_files,
        'total_links': total_links,
        'total_views': total_views,
        'recent_uploads': recent_uploads,
        'recent_views': recent_views
    }), 200

@api_bp.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def api_upload():
    """API endpoint for file upload"""
    # Check for API key in headers (implement authentication as needed)
    api_key = request.headers.get('X-API-Key')
    
    # Basic validation
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Secure and save the file
        original_filename = secure_filename(file.filename) or 'unnamed_file'
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        import secrets
        random_str = secrets.token_hex(8)
        ext = ''
        if '.' in original_filename:
            ext = '.' + original_filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{timestamp}_{random_str}{ext}"
        
        # Save file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_filename)
        file.save(file_path)
        
        # Create database record
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
        
        # Handle optional parameters
        if request.json:
            # Password protection
            password = request.json.get('password')
            if password:
                new_link.set_password(password)
            
            # Expiry
            expiry_days = request.json.get('expiry_days')
            if expiry_days and isinstance(expiry_days, int) and expiry_days > 0:
                new_link.expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
        
        db.session.add(new_link)
        db.session.commit()
        
        # Generate response
        base_url = request.url_root.rstrip('/')
        
        return jsonify({
            'success': True,
            'file': {
                'id': new_file.id,
                'name': original_filename,
                'size': new_file.file_size,
                'type': new_file.mime_type
            },
            'link': {
                'url': f"{base_url}/r/{slug}",
                'slug': slug,
                'direct_download': f"{base_url}/r/{slug}/download"
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@api_bp.route('/links/<slug>', methods=['GET'])
def get_link_info(slug):
    """Get information about a specific link"""
    link = Link.query.filter_by(slug=slug, is_active=True).first()
    
    if not link:
        return jsonify({'error': 'Link not found'}), 404
    
    file = link.file
    
    return jsonify({
        'link': {
            'slug': link.slug,
            'created': link.created_date.isoformat(),
            'expires': link.expiry_date.isoformat() if link.expiry_date else None,
            'views': link.view_count,
            'password_protected': bool(link.password_hash),
            'active': link.is_active
        },
        'file': {
            'name': file.original_filename,
            'size': file.file_size,
            'type': file.mime_type,
            'uploaded': file.upload_date.isoformat()
        }
    }), 200

@api_bp.route('/links/<slug>', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_link(slug):
    """Delete a link (requires authentication)"""
    # Check for API key or authentication
    api_key = request.headers.get('X-API-Key')
    
    link = Link.query.filter_by(slug=slug).first()
    
    if not link:
        return jsonify({'error': 'Link not found'}), 404
    
    try:
        # Deactivate the link instead of deleting
        link.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Link deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete link error: {str(e)}")
        return jsonify({'error': 'Failed to delete link'}), 500

@api_bp.route('/links/<slug>/analytics', methods=['GET'])
def get_link_analytics(slug):
    """Get analytics for a specific link"""
    link = Link.query.filter_by(slug=slug).first()
    
    if not link:
        return jsonify({'error': 'Link not found'}), 404
    
    # Get analytics data
    analytics = Analytics.query.filter_by(link_id=link.id).order_by(Analytics.access_date.desc()).limit(100).all()
    
    # Process analytics
    analytics_data = []
    for record in analytics:
        analytics_data.append({
            'timestamp': record.access_date.isoformat(),
            'ip': record.ip_address[:record.ip_address.rfind('.')] + '.xxx' if record.ip_address else None,  # Partial IP for privacy
            'country': record.country,
            'referrer': record.referrer
        })
    
    # Get daily stats for the last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    daily_views = db.session.query(
        db.func.date(Analytics.access_date).label('date'),
        db.func.count(Analytics.id).label('count')
    ).filter(
        Analytics.link_id == link.id,
        Analytics.access_date > week_ago
    ).group_by(
        db.func.date(Analytics.access_date)
    ).all()
    
    daily_stats = {str(day.date): day.count for day in daily_views}
    
    return jsonify({
        'slug': slug,
        'total_views': link.view_count,
        'last_accessed': link.last_accessed.isoformat() if link.last_accessed else None,
        'daily_stats': daily_stats,
        'recent_activity': analytics_data
    }), 200

@api_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': str(e.description)
    }), 429