from django.http import JsonResponse
from datetime import datetime
import csv
import os
import json  # Add this import at the top
from django.middleware.csrf import get_token  # Add this import
from .utils import (
    scrape_website_content, 
    generate_summary, 
    generate_tags,
    generate_short_id,
    scrape_reddit_content  # Add this import
)
from utils.supabase_client import save_to_supabase
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_csrf_token(request):
    """Return CSRF token to the frontend"""
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

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
    print(f"Received {request.method} request for Reddit analysis")
    if request.method not in ['GET', 'POST']:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                reddit_url = data.get('url')
                user_id = data.get('user_id')
                scraped_data = data.get('scraped_data')
                
                print(f"POST request received with scraped data: {bool(scraped_data)}")
                print(f"URL: {reddit_url}")
                print(f"User ID: {user_id}")
                
                if not reddit_url or not user_id or not scraped_data:
                    return JsonResponse({
                        "error": "Missing required data", 
                        "details": {
                            "url": bool(reddit_url),
                            "user_id": bool(user_id),
                            "scraped_data": bool(scraped_data)
                        }
                    }, status=400)
                
                # Use the frontend-scraped data directly instead of re-scraping
                print("Using frontend-scraped Reddit data")
                
                # No need to call scrape_reddit_content again
                # Just make sure the data has the expected format
                if not all(field in scraped_data for field in ['content', 'title', 'domain', 'author', 'featured_image']):
                    print(f"Malformed scraped_data: {list(scraped_data.keys())}")
                    return JsonResponse({"error": "Malformed scraped data"}, status=400)
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}, Body: {request.body[:100]}")
                return JsonResponse({"error": f"Invalid JSON format: {str(e)}"}, status=400)
        else:
            reddit_url = request.GET.get('url')
            user_id = request.GET.get('user_id')
            scraped_data = None
            
            print(f"GET request received for Reddit URL: {reddit_url}")
            print(f"User ID: {user_id}")
            
            if not reddit_url or not user_id:
                return JsonResponse({"error": "Missing URL or user ID"}, status=400)
            
            # Try server-side scraping as fallback
            print("Attempting server-side Reddit scraping...")
            scraped_data = scrape_reddit_content(reddit_url)
            if not scraped_data:
                print("Server-side Reddit scraping failed")
                return JsonResponse({"error": "Failed to scrape Reddit content"}, status=500)

        # Generate summary and tags using Gemini
        print("Generating summary and tags with Gemini...")
        summary = generate_summary(scraped_data['content'])
        tags = generate_tags(scraped_data['content'])
        print("Summary and tags generated successfully")

        # Prepare data for storage
        reddit_data = {
            'id': generate_short_id(),
            'user_id': user_id,
            'title': scraped_data['title'],
            'channel_name': f"{scraped_data['domain']} • u/{scraped_data['author']}",
            'video_type': 'reddit',
            'tags': ", ".join(tags),
            'summary': summary,
            'thumbnail_url': scraped_data['featured_image'],
            'original_url': reddit_url,
            'date_added': datetime.now().isoformat()
        }

        # Save to Supabase
        print("Saving Reddit data to Supabase...")
        result = save_to_supabase(reddit_data)
        if not result:
            print("Failed to save to Supabase")
            return JsonResponse({"error": "Failed to save to database"}, status=500)
        print("Successfully saved to Supabase")

        return JsonResponse(reddit_data)

    except Exception as e:
        print(f"Unexpected error in analyze_reddit: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)