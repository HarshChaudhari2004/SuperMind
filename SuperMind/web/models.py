from django.db import models

class WebsiteData(models.Model):
    ID = models.CharField(max_length=8, unique=True)
    Title = models.CharField(max_length=255)
    Description = models.TextField()
    Channel_Name = models.CharField(max_length=255, blank=True)
    Thumbnail_URL = models.URLField(blank=True)
    Video_Type = models.CharField(max_length=100, blank=True)
    Top_100_Comments = models.TextField(blank=True)
    Tags = models.TextField()
    Summary = models.TextField()
    Created_At = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.Title
