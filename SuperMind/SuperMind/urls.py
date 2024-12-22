"""
URL configuration for SuperMind project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from video_summary import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include('video_summary.urls')),  # Include video_summary app URLs
    path('', views.home, name='home'),  # Add this line to handle the root URL
    path('instagram/', include('instagram.urls')),  # Include new app URLs
    path('web/', include('web.urls')), # New website analysis URLs
    path('URL_handler/', include('URL_handler.urls')),  # Include the URL handler app's URLs
    path('', include('URL_handler.urls')),
]
