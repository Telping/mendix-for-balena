# Quick Start Guide

Get Boxty's Diary running in under 5 minutes!

## Option 1: Local Development (Fastest)

```bash
# Clone and enter directory
cd boxty-diary

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py
```

Open http://localhost:5000 and start adding memories!

## Option 2: Docker (Recommended for Testing)

```bash
cd boxty-diary
docker-compose up -d
```

Open http://localhost:5000

## Option 3: Deploy to Raspberry Pi (Best for Production)

```bash
# Install Balena CLI
npm install -g balena-cli

# Login and create app
balena login
balena app create boxty-diary --type raspberrypi4-64

# Deploy
cd boxty-diary
balena push boxty-diary
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions.

## First Steps

1. **Create your first entry**:
   - Click "Add New Memory"
   - Upload Boxty's photo
   - Add location and description
   - Save!

2. **Try the map view**:
   - Click "Map" in navigation
   - See all locations Boxty has visited

3. **Customize**:
   - Edit colors in `app/templates/base.html`
   - Change app name throughout files
   - Add your own features!

## Need Help?

- Full documentation: [README.md](README.md)
- Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Report issues: Create a GitHub issue

Enjoy documenting Boxty's journey! 🐾
