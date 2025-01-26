#!/usr/bin/env bash
set -e
cd SuperMind
pwd

echo "Installing Django dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django server..."
