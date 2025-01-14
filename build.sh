#!/usr/bin/env bash
set -e

echo "Installing Django dependencies..."
pip install -r requirements.txt

echo "Building React app..."
cd UI/supermind-ui
npm install
npm run build
cd ../..


echo "Collecting static files..."
python SuperMind/manage.py collectstatic --noinput

echo "Starting Django server..."
echo "Current directory:"
