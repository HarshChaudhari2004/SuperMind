from django.http import JsonResponse
from datetime import datetime
import csv
import os
from .utils import (
    scrape_website_content, 
    generate_summary, 
    generate_tags,
    generate_short_id,
    scrape_reddit_content  # Add this import
)
from utils.supabase_client import save_to_supabase
from django.views.decorators.csrf import csrf_exempt

def save_to_csv(video_data, filename="video_data.csv"):
    """Save data to CSV file"""
    fieldnames = [
        'id', 'user_id', 'title', 'channel_name', 'video_type',
        'tags', 'summary', 'thumbnail_url', 'original_url', 'date_added'
    ]
    
    file_exists = os.path.exists(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        print("Saving data:", video_data)  # Add debug logging
        writer.writerow(video_data)

def analyze_website(request):  # Renamed from generate_web_summary to match urls.py
    """Analyze website content and save to CSV"""
    website_url = request.GET.get('url')
    user_id = request.GET.get('user_id')  # Get user_id from query params
    
    if not website_url:
        return JsonResponse({"error": "No URL provided"}, status=400)
    
    if not user_id:
        return JsonResponse({"error": "User ID required"}, status=400)

    try:
        scraped_data = scrape_website_content(website_url)
        if not scraped_data:
            return JsonResponse({"error": "Failed to scrape website"}, status=500)

        summary = generate_summary(scraped_data['content'])
        tags = generate_tags(scraped_data['content'])

        website_data = {
            'id': generate_short_id(),
            'user_id': user_id,  # Use the provided user_id
            'title': scraped_data['title'],
            'channel_name': scraped_data['domain'],
            'video_type': 'website',
            'tags': ", ".join(tags),
            'summary': summary,
            'thumbnail_url': scraped_data['featured_image'],
            'original_url': website_url,
            'date_added': datetime.now().isoformat()
        }

        # Save to Supabase first
        result = save_to_supabase(website_data)
        if not result:
            return JsonResponse({"error": "Failed to save to database"}, status=500)

        return JsonResponse(website_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt  # Add this decorator
def analyze_reddit(request):
    """Analyze Reddit content and save to database"""
    if request.method not in ['GET', 'POST']:
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    # Get parameters from either GET or POST
    reddit_url = request.GET.get('url') or request.POST.get('url')
    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    
    if not reddit_url:
        return JsonResponse({"error": "No Reddit URL provided"}, status=400)
    
    if not user_id:
        return JsonResponse({"error": "User ID required"}, status=400)

    try:
        scraped_data = scrape_reddit_content(reddit_url)
        if not scraped_data:
            return JsonResponse({"error": "Failed to scrape Reddit content"}, status=500)

        summary = generate_summary(scraped_data['content'])
        tags = generate_tags(scraped_data['content'])

        # Updated mapping for Reddit data
        reddit_data = {
            'id': generate_short_id(),
            'user_id': user_id,
            'title': scraped_data['title'],
            'channel_name': f"{scraped_data['domain']} • u/{scraped_data['author']}", # Combine subreddit and username
            'video_type': 'reddit',
            'tags': ", ".join(tags),
            'summary': summary,
            'thumbnail_url': scraped_data['featured_image'],
            'original_url': reddit_url,
            'date_added': datetime.now().isoformat()
            # Removed author field since we're including it in channel_name
        }

        # Save to Supabase
        result = save_to_supabase(reddit_data)
        if not result:
            return JsonResponse({"error": "Failed to save to database"}, status=500)

        return JsonResponse(reddit_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)