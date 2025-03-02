from django.urls import path
from . import views

urlpatterns = [
    path('api/analyze-website/', views.analyze_website, name='analyze_website'),
    path('api/analyze-reddit/', views.analyze_reddit, name='analyze_reddit'),
]
