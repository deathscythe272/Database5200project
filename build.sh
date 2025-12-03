#!/usr/bin/env bash
# Build script for Render.com

set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database and seed demo data
python -c "
from run import app, db
from app.models import User

with app.app_context():
    db.create_all()
    
    # Check if demo data exists
    if not User.query.filter_by(username='admin').first():
        # Run seed command
        import subprocess
        subprocess.run(['flask', 'seed-demo'], check=True)
"

echo "Build completed successfully!"
