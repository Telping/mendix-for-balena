# Boxty's Diary

A beautiful digital diary application to track the life and adventures of Boxty the dog. Upload photos, videos, track locations, and create a timeline of precious memories.

## Features

- 📸 Upload photos and videos
- 🗺️ Geolocation tracking with interactive maps
- 🏷️ Tag entries for easy organization
- 📱 Mobile-friendly responsive design
- 🐾 Beautiful UI themed for your furry friend with hero section
- 🗓️ Timeline view of all memories
- 🌍 Map view showing all locations visited
- 🖼️ Customizable homepage with Boxty's photo

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd boxty-diary
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
# Edit .env and set your SECRET_KEY
```

5. (Optional) Add Boxty's hero photo:
```bash
./add-boxty-photo.sh
# Or manually: cp your-photo.jpg app/static/images/boxty-hero.jpg
```

6. Run the application:
```bash
python run.py
# Or use the quick start script: ./start-local.sh
```

7. Open your browser and navigate to `http://localhost:5000`

## Docker Deployment

### Local Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t boxty-diary .

# Run the container
docker run -d -p 5000:5000 \
  -v $(pwd)/uploads:/app/app/static/uploads \
  -e SECRET_KEY=your-secret-key \
  boxty-diary
```

## Raspberry Pi Deployment with Balena

Balena makes it incredibly easy to deploy containerized applications to Raspberry Pi devices with automatic updates and fleet management.

### Prerequisites

1. A Balena account (sign up at https://balena.io)
2. Balena CLI installed: `npm install -g balena-cli`
3. Raspberry Pi 4 (or Pi 3)
4. SD card (16GB+ recommended)

### Step 1: Create Balena Application

```bash
# Login to Balena
balena login

# Create a new application
balena app create boxty-diary --type raspberrypi4-64
```

### Step 2: Add Your Device

1. Go to your Balena dashboard
2. Click "Add device"
3. Download the Balena OS image
4. Flash it to your SD card using Balena Etcher
5. Insert SD card into your Pi and power it on
6. Wait for device to appear in your dashboard (2-5 minutes)

### Step 3: Deploy the Application

```bash
# Add Balena remote
cd boxty-diary
balena app boxty-diary  # Note your app name

# Deploy to all devices in the fleet
balena push boxty-diary
```

That's it! Balena will:
- Build the Docker container in the cloud
- Push it to your Raspberry Pi
- Start the application automatically
- Keep it running with auto-restart
- Handle updates when you push new code

### Step 4: Configure Environment Variables

In your Balena dashboard:
1. Go to your application
2. Click "Environment Variables"
3. Add these variables:
   - `SECRET_KEY`: A secure random string
   - `FLASK_ENV`: `production`

### Step 5: Access Your Application

#### Option A: Local Network Access
- Find your Pi's IP address in the Balena dashboard
- Access via `http://<pi-ip-address>`

#### Option B: Public URL (Recommended)
Balena provides a public URL for each device:
1. In the Balena dashboard, click on your device
2. Enable "Public Device URL"
3. Access your diary from anywhere using the provided URL

#### Option C: Custom Domain with Cloudflare Tunnel
For a custom domain without exposing your home IP:

1. Install Cloudflare Tunnel on your Pi (can be added as another service)
2. Point your domain to the tunnel
3. Access via your custom domain

### Balena Best Practices

**Persistent Storage**: Uploads and database are stored in named volumes, so they persist across updates.

**View Logs**:
```bash
balena logs <device-uuid> --tail
```

**SSH into Device**:
```bash
balena ssh <device-uuid>
```

**Update Application**:
Just push changes to trigger a new build:
```bash
git commit -am "Update feature"
balena push boxty-diary
```

**Fleet Management**:
- Update all devices simultaneously
- Roll back to previous releases
- Monitor device health
- Remote restart/reboot

## AWS Deployment

### Prerequisites

1. AWS Account
2. AWS CLI configured
3. GitHub repository with secrets configured

### Setup AWS Infrastructure

#### 1. Create ECR Repository

```bash
aws ecr create-repository --repository-name boxty-diary --region us-east-1
```

#### 2. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name boxty-diary-cluster --region us-east-1
```

#### 3. Create Task Definition

Create a file `ecs-task-definition.json`:

```json
{
  "family": "boxty-diary-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "boxty-diary",
      "image": "<YOUR-ECR-REPO-URI>:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SECRET_KEY",
          "value": "your-secret-key-here"
        },
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/boxty-diary",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task:
```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

#### 4. Create ECS Service

```bash
aws ecs create-service \
  --cluster boxty-diary-cluster \
  --service-name boxty-diary-service \
  --task-definition boxty-diary-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Configure GitHub Actions

Add these secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

The GitHub Actions workflow will automatically:
1. Build Docker image
2. Push to ECR
3. Update ECS service
4. Deploy new version

### Alternative: AWS Elastic Beanstalk

For simpler deployment without containers:

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 boxty-diary --region us-east-1

# Create environment
eb create boxty-diary-env

# Deploy
eb deploy
```

## Storage Considerations

### Raspberry Pi
- Use external USB drive for uploads if SD card space is limited
- Mount external drive to `/app/app/static/uploads`
- Consider automatic backup to cloud storage (S3, Backblaze B2)

### AWS
- Use EFS (Elastic File System) for persistent uploads
- Or use S3 for media storage (requires code modifications)
- RDS PostgreSQL for production database

## Backup Strategy

### For Raspberry Pi:

**Automated Backup Script** (create `backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/mnt/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
cp /path/to/boxty.db "$BACKUP_DIR/boxty_$DATE.db"

# Backup uploads
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /path/to/uploads

# Keep only last 30 days
find "$BACKUP_DIR" -type f -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### For AWS:
- Enable automated RDS snapshots
- Enable S3 versioning for uploads
- Use AWS Backup service

## Customization

### Change Colors
Edit the CSS variables in [app/templates/base.html](app/templates/base.html):
```css
:root {
    --boxty-brown: #8B4513;
    --boxty-light: #D2691E;
    --boxty-cream: #FFF8DC;
}
```

### Add More Fields
1. Update models in [app/models.py](app/models.py)
2. Create migration: `flask db migrate -m "Add new field"`
3. Apply migration: `flask db upgrade`
4. Update forms in templates

## Troubleshooting

### Issue: Cannot upload large videos
**Solution**: Increase `MAX_CONTENT_LENGTH` in [app/__init__.py](app/__init__.py)

### Issue: Database locked error
**Solution**: Switch to PostgreSQL for production:
```bash
DATABASE_URL=postgresql://user:pass@host/dbname
```

### Issue: Running out of space on Raspberry Pi
**Solution**:
- Use external USB storage
- Compress older videos
- Implement automatic cleanup of old uploads

### Issue: Balena deployment fails
**Solution**:
- Check logs: `balena logs <device-uuid>`
- Ensure device is online in dashboard
- Try rebuilding: `balena push boxty-diary --nocache`

## Development

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback
flask db downgrade
```

### Running Tests

```bash
# TODO: Add tests
pytest
```

## Tech Stack

- **Backend**: Flask 3.0, SQLAlchemy
- **Frontend**: Bootstrap 5, Leaflet.js for maps
- **Database**: SQLite (development), PostgreSQL (production)
- **Deployment**: Docker, Balena, AWS ECS
- **CI/CD**: GitHub Actions

## License

MIT License - Feel free to use this for your own pet diary!

## Contributing

Pull requests welcome! Please feel free to submit improvements.

---

Made with ❤️ for Boxty the adorable pup!
