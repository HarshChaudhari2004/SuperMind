from django.urls import path
from . import views

urlpatterns = [
    path('api/analyze-instagram/', views.instagram_analysis_view, name='instagram'),
]
