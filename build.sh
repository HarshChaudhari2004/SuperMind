#!/usr/bin/env bash
set -e

echo "Installing Django dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python SuperMind/manage.py collectstatic --noinput

echo "Starting Django server..."
cd SuperMind