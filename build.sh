#!/usr/bin/env bash
set -e
cd SuperMind
echo "current directory is: $(pwd)"
echo "list of files in current directory is: $(ls)"

echo "Installing Django dependencies..."
pip install -r requirements.txt

# echo "Collecting static files..."
# python manage.py collectstatic --noinput

echo "Starting Django server..."
