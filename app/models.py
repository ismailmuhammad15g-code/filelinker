"""
Database Models
Defines the data structures for files, links, and analytics tracking
"""
import os
import string
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class File(db.Model):
    """Model for uploaded files"""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    upload_ip = db.Column(db.String(45))
    
    # Relationship with links
    links = db.relationship('Link', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<File {self.original_filename}>'
    
    def get_file_extension(self):
        """Extract file extension from filename, with MIME type fallback"""
        # First try to get extension from filename
        if '.' in self.original_filename:
            return self.original_filename.rsplit('.', 1)[1].lower()
        
        # Fallback to MIME type detection
        if self.mime_type:
            mime_to_ext = {
                'image/png': 'png',
                'image/jpeg': 'jpg',
                'image/jpg': 'jpg',
                'image/gif': 'gif',
                'image/bmp': 'bmp',
                'image/svg+xml': 'svg',
                'image/webp': 'webp',
                'text/html': 'html',
                'text/css': 'css',
                'text/javascript': 'js',
                'application/javascript': 'js',
                'application/json': 'json',
                'application/xml': 'xml',
                'text/xml': 'xml',
                'text/plain': 'txt',
                'application/pdf': 'pdf',
                'audio/mpeg': 'mp3',
                'audio/wav': 'wav',
                'audio/ogg': 'ogg',
                'audio/mp4': 'm4a',
                'video/mp4': 'mp4',
                'video/webm': 'webm',
                'video/ogg': 'ogg',
                'video/avi': 'avi',
                'video/quicktime': 'mov',
            }
            return mime_to_ext.get(self.mime_type.lower(), '')
        
        return ''
    
    def is_previewable(self):
        """Check if file can be previewed"""
        ext = self.get_file_extension()
        return ext in [
            # Web files
            'html', 'htm', 'css', 'js', 'json', 'xml',
            # Text files
            'txt', 'md', 'py', 'java', 'cpp', 'c', 'h', 'cs', 'php', 'rb', 'go', 'rs',
            # Images
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
            # Documents
            'pdf',
            # Audio
            'mp3', 'wav', 'ogg', 'm4a',
            # Video
            'mp4', 'webm', 'ogg', 'avi', 'mov'
        ]
    
    def get_preview_type(self):
        """Get the type of preview for this file"""
        ext = self.get_file_extension()
        
        if ext in ['html', 'htm']:
            return 'html'
        elif ext in ['css', 'js', 'json', 'xml', 'txt', 'md', 'py', 'java', 'cpp', 'c', 'h', 'cs', 'php', 'rb', 'go', 'rs']:
            return 'text'
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
            return 'image'
        elif ext == 'pdf':
            return 'pdf'
        elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
            return 'audio'
        elif ext in ['mp4', 'webm', 'ogg', 'avi', 'mov']:
            return 'video'
        else:
            return 'unsupported'

class Link(db.Model):
    """Model for shareable links"""
    __tablename__ = 'links'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(20), unique=True, nullable=False, index=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=True)
    
    # Security
    password_hash = db.Column(db.String(128), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Analytics
    view_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Relationship with analytics
    analytics = db.relationship('Analytics', backref='link', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Link {self.slug}>'
    
    @staticmethod
    def generate_slug(length=8):
        """Generate a unique URL-safe slug"""
        alphabet = string.ascii_letters + string.digits
        while True:
            slug = ''.join(secrets.choice(alphabet) for _ in range(length))
            if not Link.query.filter_by(slug=slug).first():
                return slug
    
    def set_password(self, password):
        """Set password protection for the link"""
        if password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password for protected link"""
        if not self.password_hash:
            return True
        return check_password_hash(self.password_hash, password)
    
    def increment_views(self):
        """Increment view counter and update last accessed time"""
        self.view_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.commit()
    
    def is_expired(self):
        """Check if link has expired"""
        if not self.expiry_date:
            return False
        return datetime.utcnow() > self.expiry_date
    
    def get_full_url(self, base_url):
        """Generate full shareable URL"""
        return f"{base_url}/r/{self.slug}"

class Analytics(db.Model):
    """Model for tracking link analytics"""
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey('links.id'), nullable=False)
    access_date = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    referrer = db.Column(db.String(255))
    country = db.Column(db.String(2))  # ISO country code
    
    def __repr__(self):
        return f'<Analytics {self.id} for Link {self.link_id}>'

class User(db.Model):
    """Model for registered users"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Storage limits
    storage_used = db.Column(db.BigInteger, default=0)  # in bytes
    max_storage = db.Column(db.BigInteger, default=1073741824)  # 1GB default
    
    # Premium status
    is_premium = db.Column(db.Boolean, default=False)
    
    # User files and websites relationship
    user_files = db.relationship('UserFile', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    websites = db.relationship('Website', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @property
    def username(self):
        """Get username from email or full name"""
        if self.full_name:
            return self.full_name.split()[0]  # First name
        return self.email.split('@')[0]  # Email prefix
    
    def set_password(self, password):
        """Set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify user password"""
        return check_password_hash(self.password_hash, password)
    
    def can_upload(self, file_size):
        """Check if user has enough storage space"""
        return (self.storage_used + file_size) <= self.max_storage
    
    def update_storage(self, size_delta):
        """Update user's storage usage"""
        self.storage_used = max(0, self.storage_used + size_delta)
        db.session.commit()
    
    def recalculate_storage(self):
        """Recalculate storage usage from actual files"""
        total = 0
        # Sum up all user's uploaded files
        for user_file in self.user_files:
            if user_file.file:
                total += user_file.file.file_size
        
        # Sum up all website files
        for website in self.websites:
            for website_file in website.website_files:
                if website_file.file:
                    total += website_file.file.file_size
        
        self.storage_used = total
        db.session.commit()
        return total

class UserFile(db.Model):
    """Association between users and their uploaded files"""
    __tablename__ = 'user_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with file
    file = db.relationship('File', backref='user_files')
    
    def __repr__(self):
        return f'<UserFile User:{self.user_id} File:{self.file_id}>'

class Website(db.Model):
    """Model for user-created websites"""
    __tablename__ = 'websites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(128))
    
    # Statistics
    view_count = db.Column(db.Integer, default=0)
    
    # Website files relationship
    website_files = db.relationship('WebsiteFile', backref='website', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Website {self.name}>'
    
    @staticmethod
    def generate_slug(name):
        """Generate URL-safe slug from website name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Ensure uniqueness
        base_slug = slug[:45]
        counter = 1
        while Website.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def set_password(self, password):
        """Set password protection for the website"""
        if password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password for protected website"""
        if not self.password_hash:
            return True
        return check_password_hash(self.password_hash, password)
    
    def get_url(self, base_url):
        """Generate full URL for the website"""
        return f"{base_url}/site/{self.slug}"

class WebsiteFile(db.Model):
    """Files associated with a website"""
    __tablename__ = 'website_files'
    
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)  # Path within website structure
    is_index = db.Column(db.Boolean, default=False)  # Is this the index.html file?
    
    # Relationship with file
    file = db.relationship('File', backref='website_files')
    
    def __repr__(self):
        return f'<WebsiteFile Website:{self.website_id} File:{self.file_id}>'
