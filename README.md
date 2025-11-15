# FileLink Pro - Professional File Sharing Platform

A modern, corporate-style file sharing platform that creates permanent links for any file type with HTML preview support, password protection, and detailed analytics.

## Features

- 🔗 **Permanent Links**: Generate permanent, shareable links that never expire
- 👁️ **HTML Preview**: Preview HTML, CSS, and JavaScript files directly in browser
- 🔒 **Secure Sharing**: Password protect files for enhanced security
- 📊 **Analytics**: Track views, downloads, and engagement metrics
- ⚡ **Fast Upload**: Support for files up to 100MB
- 🌍 **Global Access**: Access files from anywhere in the world
- 📱 **Responsive Design**: Works perfectly on desktop and mobile devices

## Tech Stack

- **Backend**: Python 3.11 + Flask
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3 (custom), Vanilla JavaScript
- **Server**: Gunicorn + Nginx
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Python 3.8+ or Docker
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/filelink-pro.git
   cd filelink-pro
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python -m app
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Web app: `http://localhost:5000`
   - PostgreSQL: `localhost:5432`

### Production Deployment

#### Railway Deployment (Recommended)

Deploy to Railway with one click:

1. Push your code to GitHub
2. Visit [Railway.app](https://railway.app) and create a new project
3. Select "Deploy from GitHub repo"
4. Add required environment variables (see DEPLOYMENT.md)
5. Railway will automatically deploy using the Procfile

**Important:** See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed Railway deployment instructions, including:
- Environment variable configuration
- Database setup
- File storage with Railway Volumes
- Troubleshooting common issues

#### Docker Deployment

1. **Update environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Build and run in production mode**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Set up SSL certificates**
   Place your SSL certificates in the `ssl/` directory and update `nginx.conf`

## API Documentation

### Upload File
- **POST** `/api/upload`
- **Headers**: `Content-Type: multipart/form-data`
- **Body**: `file`, `password` (optional), `expiry_days` (optional)

### Get Link Info
- **GET** `/api/links/{slug}`

### Get Statistics
- **GET** `/api/stats`

### Get Link Analytics
- **GET** `/api/links/{slug}/analytics`

## Project Structure

```
filelink-pro/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # Database models
│   ├── routes/            # Blueprint routes
│   │   ├── main.py        # Main pages
│   │   ├── upload.py      # Upload functionality
│   │   ├── share.py       # File sharing
│   │   └── api.py         # REST API
│   ├── templates/         # Jinja2 templates
│   └── static/            # CSS, JS, images
├── migrations/            # Database migrations
├── uploads/              # Uploaded files storage
├── tests/                # Test files
├── config.py             # Configuration
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose config
├── gunicorn_config.py    # Gunicorn settings
└── README.md            # This file
```

## Configuration

Key configuration options in `config.py`:

- `MAX_CONTENT_LENGTH`: Maximum file size (default: 100MB)
- `UPLOAD_FOLDER`: Directory for file storage
- `LINK_EXPIRY_DAYS`: Default link expiry (0 for permanent)
- `ENABLE_ANALYTICS`: Enable/disable analytics tracking
- `ENABLE_PASSWORD_PROTECTION`: Enable/disable password protection

## Security Considerations

- All uploaded files are stored with unique filenames
- Password protection uses bcrypt hashing
- Rate limiting on upload endpoints
- CSRF protection enabled
- SQL injection prevention via SQLAlchemy ORM
- XSS protection in templates

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@filelinkpro.com or open an issue in the GitHub repository.

## Acknowledgments

- Flask community for the excellent framework
- Contributors and testers
- Open source community

---

**Built with ❤️ by FileLink Pro Team**