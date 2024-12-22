from django.urls import path
from . import views

urlpatterns = [
    path('api/save-user-notes/', views.save_user_notes, name='save_user_notes'),
    path('api/instagram-data/', views.get_instagram_data, name='get_instagram_data'),
    path('api/video-data/', views.get_video_data, name='get_video_data'),
]