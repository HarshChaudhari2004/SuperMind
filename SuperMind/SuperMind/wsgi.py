"""
WSGI config for SuperMind project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SuperMind.SuperMind.settings")

# application = get_wsgi_application()

import os
import sys
from django.core.wsgi import get_wsgi_application

# Explicitly add the SuperMind directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SuperMind'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SuperMind.settings')

application = get_wsgi_application()
