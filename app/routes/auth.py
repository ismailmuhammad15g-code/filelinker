"""
Authentication Routes Blueprint
Handles user registration, login, logout, and session management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from functools import wraps
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        # Validation
        if not email or not password or not full_name:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user = User(
            email=email,
            full_name=full_name,
            is_admin=False,
            storage_used=0,
            max_storage=1073741824  # 1GB default
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log the user in
        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        session['user_name'] = new_user.full_name
        session['is_admin'] = new_user.is_admin
        
        flash('Registration successful! Welcome to FileLink Pro!', 'success')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Special admin account
        if email == 'admin' and password == 'admin123':
            # Check if admin exists, if not create it
            admin = User.query.filter_by(email='admin@filelinkpro.com').first()
            if not admin:
                admin = User(
                    email='admin@filelinkpro.com',
                    full_name='Administrator',
                    is_admin=True,
                    storage_used=0,
                    max_storage=10737418240  # 10GB for admin
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
            
            session['user_id'] = admin.id
            session['user_email'] = admin.email
            session['user_name'] = admin.full_name
            session['is_admin'] = True
            
            if remember:
                session.permanent = True
            
            flash('Welcome back, Administrator!', 'success')
            return redirect(url_for('auth.admin_panel'))
        
        # Regular user login
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been deactivated.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.full_name
        session['is_admin'] = user.is_admin
        
        if remember:
            session.permanent = True
        
        flash(f'Welcome back, {user.full_name}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        if user.is_admin:
            return redirect(url_for('auth.admin_panel'))
        else:
            return redirect(url_for('auth.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Get user's files and websites
    from app.models import UserFile, Website, File, Link
    
    user_files = db.session.query(File, Link).join(
        UserFile, UserFile.file_id == File.id
    ).join(
        Link, Link.file_id == File.id
    ).filter(
        UserFile.user_id == user.id
    ).order_by(File.upload_date.desc()).limit(10).all()
    
    user_websites = Website.query.filter_by(
        user_id=user.id, 
        is_published=True
    ).order_by(Website.created_date.desc()).all()
    
    # Recalculate storage usage from actual files
    user.recalculate_storage()
    
    # Calculate storage usage
    total_storage = user.max_storage
    used_storage = user.storage_used
    storage_percentage = (used_storage / total_storage * 100) if total_storage > 0 else 0
    
    return render_template('auth/dashboard.html',
                         user=user,
                         user_files=user_files,
                         user_websites=user_websites,
                         storage_percentage=storage_percentage,
                         used_storage=used_storage,
                         total_storage=total_storage)

@auth_bp.route('/admin')
@admin_required
def admin_panel():
    """Admin panel"""
    from app.models import File, Link, Website
    
    # Get statistics
    total_users = User.query.count()
    total_files = File.query.count()
    total_links = Link.query.count()
    total_websites = Website.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_date.desc()).limit(10).all()
    
    # Get recent files
    recent_files = db.session.query(File, Link).join(
        Link, Link.file_id == File.id
    ).order_by(File.upload_date.desc()).limit(10).all()
    
    # Get recent websites
    recent_websites = Website.query.order_by(Website.created_date.desc()).limit(10).all()
    
    return render_template('auth/admin.html',
                         total_users=total_users,
                         total_files=total_files,
                         total_links=total_links,
                         total_websites=total_websites,
                         recent_users=recent_users,
                         recent_files=recent_files,
                         recent_websites=recent_websites)

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    full_name = request.form.get('full_name')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    if full_name:
        user.full_name = full_name
        session['user_name'] = full_name
    
    if current_password and new_password:
        if user.check_password(current_password):
            if len(new_password) >= 6:
                user.set_password(new_password)
                flash('Password updated successfully.', 'success')
            else:
                flash('New password must be at least 6 characters.', 'danger')
        else:
            flash('Current password is incorrect.', 'danger')
    
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/file/<int:file_id>/manage')
@login_required
def manage_file(file_id):
    """Show file details and management options"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    from app.models import UserFile, File, Link
    
    # Get file and ensure user owns it
    user_file = UserFile.query.filter_by(
        user_id=user.id,
        file_id=file_id
    ).first_or_404()
    
    file = File.query.get_or_404(file_id)
    link = Link.query.filter_by(file_id=file.id).first()
    
    # Calculate deletion date (30 days for free, 365 for premium)
    deletion_days = 365 if user.is_premium else 30
    deletion_policy = f"This file will be permanently deleted from our servers in {deletion_days} days for {'Pro' if user.is_premium else 'Free'} plan users."
    
    return render_template('file/manage.html',
                         file=file,
                         link=link,
                         user=user,
                         deletion_policy=deletion_policy,
                         deletion_days=deletion_days)

@auth_bp.route('/file/<int:file_id>/update-link', methods=['POST'])
@login_required
def update_link_settings(file_id):
    """Update link settings (password, expiry)"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    from app.models import UserFile, File, Link
    from datetime import datetime, timedelta
    
    # Get file and ensure user owns it
    user_file = UserFile.query.filter_by(
        user_id=user.id,
        file_id=file_id
    ).first_or_404()
    
    file = File.query.get_or_404(file_id)
    link = Link.query.filter_by(file_id=file.id).first()
    
    if not link:
        flash('Link not found.', 'danger')
        return redirect(url_for('auth.manage_file', file_id=file_id))
    
    # Get form data
    password = request.form.get('password', '').strip()
    remove_password = request.form.get('remove_password') == 'on'
    expiry_days = request.form.get('expiry_days', type=int)
    
    try:
        # Update password
        if remove_password:
            link.password_hash = None
            flash('Password protection removed.', 'success')
        elif password:
            link.set_password(password)
            flash('Password protection updated.', 'success')
        
        # Update expiry
        if expiry_days and expiry_days > 0:
            link.expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
            flash(f'Link will expire in {expiry_days} days.', 'success')
        elif expiry_days == 0:
            link.expiry_date = None
            flash('Link expiry removed.', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating link settings: {str(e)}', 'danger')
    
    return redirect(url_for('auth.manage_file', file_id=file_id))

@auth_bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete a user's file"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    from app.models import UserFile, File, Link
    import os
    from flask import current_app
    
    # Get file and ensure user owns it
    user_file = UserFile.query.filter_by(
        user_id=user.id,
        file_id=file_id
    ).first_or_404()
    
    file = File.query.get_or_404(file_id)
    
    try:
        # Update user storage first
        if user.storage_used and user.storage_used >= file.file_size:
            user.storage_used -= file.file_size
        else:
            user.storage_used = 0
        
        # Delete physical file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.stored_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete UserFile relationship first
        db.session.delete(user_file)
        
        # Delete the file (this will cascade delete links and analytics)
        db.session.delete(file)
        
        # Commit all changes
        db.session.commit()
        
        flash('File deleted successfully! 🗑️', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting file: {e}")  # For debugging
        flash(f'Error deleting file: {str(e)}', 'danger')
    
    return redirect(url_for('auth.dashboard'))
