#!/usr/bin/env bash
set -e
cd SuperMind
pwd

echo "Installing Django dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python SuperMind/manage.py collectstatic --noinput

echo "Starting Django server..."
cd SuperMind
