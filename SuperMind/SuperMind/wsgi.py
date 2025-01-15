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

print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SuperMind.settings')

application = get_wsgi_application()
