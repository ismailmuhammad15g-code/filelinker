# FileLink Pro - Railway Deployment Guide

## Prerequisites
- Railway account
- GitHub repository

## Quick Deployment

Railway automatically detects and deploys Flask applications. This guide will help you deploy FileLink Pro successfully.

## Environment Variables

Set these environment variables in Railway dashboard:

```
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here-change-this
DATABASE_URL=sqlite:///filelink.db
UPLOAD_FOLDER=uploads
ENABLE_ANALYTICS=True
APP_VERSION=1.0.0
MAX_CONTENT_LENGTH=104857600
```

**Important Notes:**
- Railway provides a `PORT` environment variable automatically - don't set it manually
- The application is configured to use this PORT automatically
- For production use, consider using PostgreSQL instead of SQLite

## Deployment Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ismailmuhammad15g-code/filelinker.git
git push -u origin main
```

### 2. Deploy on Railway

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect the Flask app and use the configuration
6. Add the environment variables listed above in the "Variables" tab
7. Click "Deploy"

Railway will automatically:
- Install dependencies from requirements.txt
- Use the Procfile to start the application with Gunicorn
- Bind to the correct PORT
- Provide HTTPS by default

### 3. Database Setup

The application automatically creates database tables on first run. For initial setup:

1. Wait for the first deployment to complete
2. Check the logs to confirm successful startup
3. Access your app at: `https://your-app.railway.app`
4. The default admin account will be created automatically:
   - Email: `admin@filelinkpro.com`
   - Username: `admin`
   - Password: `admin123`

**⚠️ IMPORTANT: Change the admin password immediately after first login!**

## File Storage

**Important:** Railway uses ephemeral storage by default. Uploaded files will be lost when the container restarts unless you use persistent storage.

### Options for Persistent File Storage:

1. **Railway Volumes** (Recommended for Railway)
   - Add a volume in Railway dashboard
   - Mount it to `/app/uploads`
   - Files will persist across deployments

2. **External Storage Services**
   - AWS S3
   - Cloudflare R2
   - Google Cloud Storage
   - DigitalOcean Spaces

### Setting Up Railway Volume:

1. In Railway dashboard, go to your service
2. Click "Variables" tab
3. Click "Add Volume"
4. Set mount path to: `/app/uploads`
5. Redeploy your application

## Monitoring

- **View logs:** Click on your service → "Logs" tab
- **Monitor resources:** Dashboard shows CPU/Memory usage
- **Check deployments:** See deployment history and status

## Troubleshooting

### Application won't start
- Check that all environment variables are set correctly
- Review logs for specific error messages
- Ensure SECRET_KEY is set

### File upload errors
- Check MAX_CONTENT_LENGTH setting (100MB default)
- Verify uploads directory exists
- If using volumes, ensure volume is properly mounted

### Database errors
- For SQLite: Ensure write permissions
- For PostgreSQL: Verify DATABASE_URL is correct
- Check logs for specific database errors

### Port binding errors
- Don't manually set PORT environment variable
- Railway provides PORT automatically
- Application is configured to use Railway's PORT

## Security Checklist

- [ ] Change SECRET_KEY from default
- [ ] Change admin password after first login
- [ ] Review MAX_CONTENT_LENGTH for your needs
- [ ] Set up persistent storage for uploads
- [ ] Enable HTTPS (automatic with Railway)
- [ ] Set SESSION_COOKIE_SECURE=True in production
- [ ] Review and configure rate limiting
- [ ] Set up regular backups

## Performance Optimization

1. **Workers:** Gunicorn is configured with optimal worker count
2. **Database:** Consider PostgreSQL for better performance
3. **File Storage:** Use external storage for large files
4. **CDN:** Use CDN for static assets
5. **Caching:** Consider adding Redis for session management

## Updating Your Deployment

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Railway will automatically detect the push and redeploy.

## Support

For issues:
- Check Railway logs first
- Review this documentation
- Check GitHub issues
- Contact Railway support for platform issues

