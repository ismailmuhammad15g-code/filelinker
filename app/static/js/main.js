/**
 * FileLink Pro - Main JavaScript
 * Minimal JS for functionality without animations
 */

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            if (mobileMenu.style.display === 'block') {
                mobileMenu.style.display = 'none';
            } else {
                mobileMenu.style.display = 'block';
            }
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!mobileMenuBtn.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.style.display = 'none';
            }
        });
        
        // Close menu when a mobile nav link is clicked
        const mobileLinks = mobileMenu.querySelectorAll('.mobile-nav-link');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.style.display = 'none';
            });
        });
    }
});

// Utility function to format file sizes
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Utility function to copy text to clipboard
function copyToClipboard(text) {
    // Try modern API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    }
    
    // Fallback to older method
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    return new Promise((resolve, reject) => {
        document.execCommand('copy') ? resolve() : reject();
        document.body.removeChild(textArea);
    });
}

// Handle smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
});

// File validation
function validateFile(file) {
    const maxSize = 100 * 1024 * 1024; // 100MB
    
    if (file.size > maxSize) {
        alert('File size exceeds 100MB limit');
        return false;
    }
    
    return true;
}

// Handle drag and drop visual feedback
document.addEventListener('DOMContentLoaded', function() {
    const dropZones = document.querySelectorAll('.upload-box, .upload-area');
    
    dropZones.forEach(zone => {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            zone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, unhighlight, false);
        });
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        this.classList.add('dragover');
    }
    
    function unhighlight(e) {
        this.classList.remove('dragover');
    }
});

// API helper functions
const API = {
    async uploadFile(file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        if (options.password) {
            formData.append('password', options.password);
        }
        
        if (options.expiry_days) {
            formData.append('expiry_days', options.expiry_days);
        }
        
        const response = await fetch('/upload/process', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        return await response.json();
    },
    
    async getLinkInfo(slug) {
        const response = await fetch(`/api/links/${slug}`);
        if (!response.ok) {
            throw new Error(`Failed to get link info: ${response.statusText}`);
        }
        return await response.json();
    },
    
    async getStats() {
        const response = await fetch('/api/stats');
        if (!response.ok) {
            throw new Error(`Failed to get stats: ${response.statusText}`);
        }
        return await response.json();
    }
};

// Expose utility functions globally
window.FileLink = {
    formatFileSize,
    copyToClipboard,
    validateFile,
    API
};