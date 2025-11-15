"""
Site Routes Blueprint
Handles viewing of published websites
"""
import os
import mimetypes
from flask import Blueprint, render_template, send_file, abort, current_app, request, Response, session
from app.models import Website, WebsiteFile, File
from app import db
from app.utils.file_organization import find_file_in_organized_structure

site_bp = Blueprint('site', __name__)

def generate_watermark_html(user):
    """Generate watermark HTML for free users"""
    username = user.username if hasattr(user, 'username') else user.full_name.split()[0] if user.full_name else user.email.split('@')[0]
    
    watermark_html = f'''
<!-- FileLink Pro Watermark -->
<div id="filelink-watermark" style="
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: linear-gradient(135deg, rgba(0, 120, 212, 0.95), rgba(16, 124, 16, 0.95));
    color: white;
    padding: 12px 16px;
    border-radius: 25px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    font-weight: 500;
    z-index: 999999;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
    cursor: pointer;
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: 280px;
" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0, 0, 0, 0.3)'" 
   onmouseout="this.style.transform='translateY(0px)'; this.style.boxShadow='0 4px 16px rgba(0, 0, 0, 0.2)'" 
   onclick="window.open('https://filelink.pro', '_blank')">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z"/>
    </svg>
    <div>
        <div style="font-size: 11px; opacity: 0.9; line-height: 1.2;">Created by <strong>{username}</strong></div>
        <div style="font-size: 12px; font-weight: 600; line-height: 1.2;">Powered by FileLink Pro</div>
    </div>
</div>

<!-- Mobile responsive watermark -->
<style>
@media (max-width: 768px) {{
    #filelink-watermark {{
        bottom: 16px !important;
        right: 16px !important;
        padding: 10px 14px !important;
        font-size: 12px !important;
        max-width: 240px !important;
    }}
    #filelink-watermark div div:first-child {{
        font-size: 10px !important;
    }}
    #filelink-watermark div div:last-child {{
        font-size: 11px !important;
    }}
}}

@media (max-width: 480px) {{
    #filelink-watermark {{
        bottom: 12px !important;
        right: 12px !important;
        left: 12px !important;
        max-width: none !important;
        justify-content: center !important;
        text-align: center !important;
    }}
}}
</style>
'''
    
    return watermark_html

@site_bp.route('/<slug>')
def view_website(slug):
    """View a published website"""
    website = Website.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Increment view count
    website.view_count += 1
    db.session.commit()
    
    # Check if password protected
    if website.password_hash:
        # Check if a session password matches the website's password
        session_key = f'website_password_{website.id}'
        
        # Check if the correct password is in the session
        if session.get(session_key) == website.password_hash:
            pass  # Password is correct, allow access
        else:
            # If not in session, check for password in query param
            password = request.args.get('password')
            if password and website.check_password(password):
                # Correct password provided, store it in session
                session[session_key] = website.password_hash
            else:
                # No valid password, render password page
                return render_template('website/password.html', website=website)
    
    # Get index file - first try marked index files, then auto-detect
    index_file = db.session.query(WebsiteFile, File).join(
        File, WebsiteFile.file_id == File.id
    ).filter(
        WebsiteFile.website_id == website.id,
        WebsiteFile.is_index == True
    ).first()
    
    # If no marked index file found, auto-detect index.html
    if not index_file:
        index_file = db.session.query(WebsiteFile, File).join(
            File, WebsiteFile.file_id == File.id
        ).filter(
            WebsiteFile.website_id == website.id,
            File.original_filename.ilike('index.html')
        ).first()
        
        # If still not found, try index.htm
        if not index_file:
            index_file = db.session.query(WebsiteFile, File).join(
                File, WebsiteFile.file_id == File.id
            ).filter(
                WebsiteFile.website_id == website.id,
                File.original_filename.ilike('index.htm')
            ).first()
        
        # If found, mark it as index for future use
        if index_file:
            website_file, file = index_file
            website_file.is_index = True
            db.session.commit()
    
    # If there's an index file, serve it directly (no template wrapper)
    if index_file:
        # Serve the actual index file content for iframe
        website_file, file = index_file
        # Use find_file_in_organized_structure to locate the file
        file_path = find_file_in_organized_structure(file.stored_filename)
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                # Fallback to latin-1 if utf-8 fails
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    content = f.read()
            
            # Compute base URL to match the index's directory (if nested)
            index_dir = ''
            if getattr(website_file, 'file_path', None):
                # Normalize to forward slashes
                normalized = website_file.file_path.replace('\\', '/')
                index_dir = '/'.join([seg for seg in normalized.split('/')[:-1] if seg])
            
            base_url = f"/site/{slug}/assets/" + (f"{index_dir}/" if index_dir else '')
            base_tag = f"<base href=\"{base_url}\">"
            
            # Inject base tag right after the opening <head ...> (case-insensitive)
            lower_content = content.lower()
            head_pos = lower_content.find('<head')
            if head_pos != -1:
                # Find the end of the head start tag
                gt_pos = content.find('>', head_pos)
                if gt_pos != -1:
                    content = content[:gt_pos+1] + base_tag + content[gt_pos+1:]
                else:
                    # As a fallback, prepend base tag
                    content = base_tag + content
            else:
                # No head tag found; prepend base and minimal head wrapper if needed
                content = f"<head>{base_tag}</head>" + content
            
            # Add watermark for free users ONLY if content doesn't already have FileLink Pro branding
            if not website.owner.is_premium:
                # Check if content already has FileLink Pro branding to avoid duplicates
                has_filelink_branding = (
                    'filelink pro' in lower_content or 
                    'filelink-pro' in lower_content or
                    'powered by filelink' in lower_content or
                    'published by' in lower_content
                )
                
                # Only add watermark if the content doesn't already have branding
                if not has_filelink_branding:
                    watermark_html = generate_watermark_html(website.owner)
                    # Inject watermark before closing body tag, or append if no body tag
                    body_close_pos = lower_content.rfind('</body>')
                    if body_close_pos != -1:
                        # Find the actual position in the original content (case-sensitive)
                        actual_pos = content.lower().rfind('</body>')
                        content = content[:actual_pos] + watermark_html + content[actual_pos:]
                    else:
                        # No closing body tag, append watermark at the end
                        content = content + watermark_html
            
            return Response(content, mimetype='text/html')
    
    # If no index file, show file listing
    website_files = db.session.query(WebsiteFile, File).join(
        File, WebsiteFile.file_id == File.id
    ).filter(
        WebsiteFile.website_id == website.id
    ).all()
    
    # Convert to files format expected by template
    files = []
    for website_file, file in website_files:
        files.append({
            'filename': file.original_filename,
            'size': file.file_size
        })
    
    return render_template('website/view.html', 
                         website=website, 
                         website_files=website_files,
                         files=files,
                         has_index=False)

@site_bp.route('/<slug>/assets/<path:filename>')
def serve_website_asset(slug, filename):
    """Serve website assets (CSS, JS, images, videos, etc.)"""
    website = Website.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    # Normalize incoming filename to use forward slashes
    normalized_filename = filename.replace('\\', '/')
    
    # Find the file by exact stored path first
    website_file = db.session.query(WebsiteFile, File).join(
        File, WebsiteFile.file_id == File.id
    ).filter(
        WebsiteFile.website_id == website.id,
        WebsiteFile.file_path == normalized_filename
    ).first()
    
    if not website_file:
        # Fallback: try by original filename (no folders)
        website_file = db.session.query(WebsiteFile, File).join(
            File, WebsiteFile.file_id == File.id
        ).filter(
            WebsiteFile.website_id == website.id,
            File.original_filename == os.path.basename(normalized_filename)
        ).first()
    
    if website_file:
        wf, file = website_file
        # Use find_file_in_organized_structure to locate the file
        file_path = find_file_in_organized_structure(file.stored_filename)
        
        if file_path and os.path.exists(file_path):
            # Determine MIME type
            mime_type = file.mime_type or mimetypes.guess_type(file.original_filename)[0] or 'application/octet-stream'
            
            # For text files (CSS, JS), read and serve as text
            if mime_type.startswith('text/') or mime_type in ['application/javascript', 'application/json']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return Response(content, mimetype=mime_type)
            else:
                # For binary files (images, videos, etc.), serve directly
                return send_file(file_path, mimetype=mime_type)
    
    abort(404)
