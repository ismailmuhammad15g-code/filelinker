# FileLink Pro - Railway Deployment Guide

## Prerequisites
- Railway account
- GitHub repository

## Environment Variables

Set these environment variables in Railway:

```
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here-change-this
DATABASE_URL=sqlite:///filelink.db
UPLOAD_FOLDER=uploads
ENABLE_ANALYTICS=True
APP_VERSION=1.0.0
MAX_CONTENT_LENGTH=104857600
```

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
5. Railway will auto-detect the Flask app
6. Add the environment variables above
7. Deploy!

### 3. Database Setup

After first deployment, run migrations:
```bash
railway run python init_db.py
```

## Post-Deployment

1. Access your app at: `https://your-app.railway.app`
2. Create admin account: Login with `admin` / `admin123`
3. Change admin password immediately!

## File Storage

For production, consider using:
- AWS S3
- Cloudflare R2
- Railway Volumes (for persistent storage)

## Monitoring

- Check logs: `railway logs`
- Monitor CPU/Memory in Railway dashboard

## Security Checklist

- [ ] Change SECRET_KEY
- [ ] Change admin password
- [ ] Set up domain with HTTPS
- [ ] Configure CORS if needed
- [ ] Set up backups
- [ ] Review file upload limits

## Support

For issues, contact support or check documentation.
