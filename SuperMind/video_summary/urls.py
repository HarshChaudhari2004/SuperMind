# video_summary/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('generate-summary/', views.generate_keywords_and_summary, name='generate_summary'),
    path('test/', views.test_connection, name='test_connection'),
]
