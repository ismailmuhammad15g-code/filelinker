"""
Main Routes Blueprint
Handles landing page, about page, and general site navigation
"""
from flask import Blueprint, render_template, current_app
from app.models import File, Link, Analytics
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page with hero section and features"""
    # Get statistics for display
    total_files = File.query.count()
    total_links = Link.query.count()
    total_views = db.session.query(db.func.sum(Link.view_count)).scalar() or 0
    
    stats = {
        'files': total_files,
        'links': total_links,
        'views': total_views
    }
    
    return render_template('landing.html', stats=stats)

@main_bp.route('/features')
def features():
    """Features page describing platform capabilities"""
    features_list = [
        {
            'icon': '🔗',
            'title': 'Permanent Links',
            'description': 'Generate permanent, shareable links that never expire'
        },
        {
            'icon': '👁️',
            'title': 'HTML Preview',
            'description': 'Preview HTML, CSS, and JavaScript files directly in the browser'
        },
        {
            'icon': '🔒',
            'title': 'Secure Sharing',
            'description': 'Password protect your files for enhanced security'
        },
        {
            'icon': '📊',
            'title': 'Analytics',
            'description': 'Track views, clicks, and download statistics'
        },
        {
            'icon': '⚡',
            'title': 'Fast Upload',
            'description': 'Quick and reliable file uploads up to 100MB'
        },
        {
            'icon': '🌍',
            'title': 'Global Access',
            'description': 'Access your files from anywhere in the world'
        }
    ]
    return render_template('features.html', features=features_list)

@main_bp.route('/pricing')
def pricing():
    """Pricing page with different tiers"""
    plans = [
        {
            'name': 'Free',
            'price': '$0',
            'features': ['10 files/month', '100MB storage', 'Basic analytics', 'Public links only'],
            'cta': 'Get Started'
        },
        {
            'name': 'Pro',
            'price': '$9',
            'features': ['Unlimited files', '10GB storage', 'Advanced analytics', 'Password protection', 'Custom slugs', 'Priority support'],
            'cta': 'Start Free Trial',
            'highlighted': True
        },
        {
            'name': 'Enterprise',
            'price': 'Custom',
            'features': ['Unlimited everything', 'Custom storage', 'API access', 'Team management', 'SLA guarantee', 'Dedicated support'],
            'cta': 'Contact Sales'
        }
    ]
    return render_template('pricing.html', plans=plans)

@main_bp.route('/docs')
def docs():
    """Documentation page"""
    return render_template('docs.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/editor')
def code_editor():
    """HTML/CSS/JS code editor and preview"""
    return render_template('code_editor.html')
