# Boxty's Diary - Project Structure

```
boxty-diary/
├── app/                          # Flask application package
│   ├── __init__.py              # App factory and configuration
│   ├── models.py                # Database models (DiaryEntry, Media, Tag)
│   ├── routes.py                # URL routes and view functions
│   ├── static/                  # Static files
│   │   ├── css/                 # Custom CSS (optional)
│   │   ├── js/                  # Custom JavaScript (optional)
│   │   └── uploads/             # User-uploaded photos and videos
│   │       └── .gitkeep        # Keep empty directory in git
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html           # Base template with navigation
│       ├── index.html          # Homepage with entry grid
│       ├── new_entry.html      # Form to create new entries
│       ├── view_entry.html     # Single entry detail view
│       └── map.html            # Interactive map of all locations
│
├── .github/                     # GitHub Actions workflows
│   └── workflows/
│       ├── aws-deploy.yml      # Auto-deploy to AWS ECS
│       └── docker-build.yml    # Test Docker builds on PRs
│
├── instance/                    # SQLite database location (created at runtime)
│   └── boxty.db                # SQLite database file
│
├── venv/                        # Python virtual environment (created at runtime)
│
├── .env                         # Environment variables (create from .env.example)
├── .env.example                # Example environment configuration
├── .gitignore                  # Git ignore rules
│
├── balena.yml                  # Balena.io fleet configuration
├── docker-compose.balena.yml   # Balena-specific Docker Compose
├── docker-compose.yml          # Local Docker Compose
├── Dockerfile                  # Docker container definition
│
├── requirements.txt            # Python dependencies
├── run.py                      # Application entry point
│
├── start-local.sh              # Quick start script for local dev
│
├── README.md                   # Main documentation
├── DEPLOYMENT.md               # Deployment guides (Balena, AWS)
├── QUICKSTART.md               # 5-minute getting started guide
└── PROJECT-STRUCTURE.md        # This file

```

## Key Files Explained

### Application Core

- **`run.py`**: Entry point that creates and runs the Flask app
- **`app/__init__.py`**: Application factory pattern, configures Flask extensions
- **`app/models.py`**: SQLAlchemy ORM models for database tables
- **`app/routes.py`**: All URL routes and business logic

### Database Models

1. **DiaryEntry**: Main entry with title, date, description, location
2. **Media**: Photos/videos linked to entries
3. **Tag**: Categorization tags with many-to-many relationship

### Templates

- **`base.html`**: Master template with navbar, styling, and common scripts
- **`index.html`**: Card grid showing all diary entries
- **`new_entry.html`**: Form with file upload and geolocation capture
- **`view_entry.html`**: Full entry view with image modal and map
- **`map.html`**: Interactive Leaflet map with paw print markers

### Deployment Configurations

- **`Dockerfile`**: Production-ready container with gunicorn
- **`docker-compose.yml`**: Local development with volume mounts
- **`docker-compose.balena.yml`**: Balena cloud with persistent volumes
- **`balena.yml`**: Balena fleet metadata and environment variables
- **`.github/workflows/`**: Automated CI/CD pipelines

## Technology Stack

### Backend
- **Flask 3.0**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Flask-Migrate**: Database migrations
- **Gunicorn**: Production WSGI server

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Leaflet.js**: Interactive maps
- **Vanilla JavaScript**: Form handling and geolocation

### Infrastructure
- **Docker**: Containerization
- **Balena**: IoT/Pi deployment platform
- **AWS ECS**: Container orchestration (optional)
- **GitHub Actions**: CI/CD automation

## Data Flow

```
User uploads photo/video
    ↓
Flask route receives multipart/form-data
    ↓
Werkzeug secures filename
    ↓
File saved to app/static/uploads/
    ↓
Media record created in database
    ↓
DiaryEntry created with relationship to Media
    ↓
Database commit
    ↓
Redirect to entry view
```

## URL Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage with all entries |
| `/entry/new` | GET, POST | Create new diary entry |
| `/entry/<id>` | GET | View single entry details |
| `/entry/<id>/delete` | POST | Delete an entry |
| `/map` | GET | Map view of all locations |
| `/api/entries` | GET | JSON API for all entries |
| `/uploads/<filename>` | GET | Serve uploaded media files |

## Database Schema

```sql
-- DiaryEntry table
CREATE TABLE diary_entry (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    date DATETIME NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    location_name VARCHAR(200),
    created_at DATETIME
);

-- Media table
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    filename VARCHAR(300) NOT NULL,
    media_type VARCHAR(20) NOT NULL,  -- 'image' or 'video'
    file_path VARCHAR(500) NOT NULL,
    entry_id INTEGER REFERENCES diary_entry(id),
    uploaded_at DATETIME
);

-- Tag table
CREATE TABLE tag (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Many-to-many association
CREATE TABLE entry_tags (
    entry_id INTEGER REFERENCES diary_entry(id),
    tag_id INTEGER REFERENCES tag(id),
    PRIMARY KEY (entry_id, tag_id)
);
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session encryption key | Random 32-char hex |
| `DATABASE_URL` | Database connection string | `sqlite:///boxty.db` |
| `FLASK_ENV` | Environment mode | `development` or `production` |

## Adding New Features

### Example: Add "Mood" Field

1. **Update model** (`app/models.py`):
```python
class DiaryEntry(db.Model):
    # ... existing fields ...
    mood = db.Column(db.String(50), nullable=True)
```

2. **Create migration**:
```bash
flask db migrate -m "Add mood field"
flask db upgrade
```

3. **Update form** (`app/templates/new_entry.html`):
```html
<select name="mood" class="form-control">
    <option>Happy</option>
    <option>Playful</option>
    <option>Sleepy</option>
</select>
```

4. **Update route** (`app/routes.py`):
```python
mood = request.form.get('mood')
entry = DiaryEntry(mood=mood, ...)
```

5. **Display** (`app/templates/view_entry.html`):
```html
<p>Mood: {{ entry.mood }}</p>
```

## Security Considerations

- ✅ CSRF protection via Flask secret key
- ✅ Secure filename sanitization with Werkzeug
- ✅ SQL injection prevention via SQLAlchemy ORM
- ✅ File type validation on upload
- ✅ File size limits configured
- ⚠️ **TODO**: Add authentication for multi-user scenarios
- ⚠️ **TODO**: Implement HTTPS in production
- ⚠️ **TODO**: Add rate limiting for uploads

## Performance Optimization Ideas

- [ ] Implement image thumbnail generation
- [ ] Add lazy loading for images
- [ ] Compress videos on upload
- [ ] Add database indexing on date field
- [ ] Implement caching with Flask-Caching
- [ ] Use CDN for static assets in production
- [ ] Add pagination for large entry collections

## Future Enhancement Ideas

- [ ] Multi-user support with authentication
- [ ] Social sharing (generate beautiful cards)
- [ ] Export diary to PDF
- [ ] Advanced search and filtering
- [ ] Timeline visualization
- [ ] Integration with pet health tracking
- [ ] Automatic photo organization by date
- [ ] Voice notes support
- [ ] Mobile app with React Native
- [ ] AI-generated captions for photos

---

Happy coding with Boxty! 🐾
