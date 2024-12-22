from django.http import JsonResponse
from datetime import datetime
import csv
import os
from .utils import (
    scrape_website_content, 
    generate_summary, 
    generate_tags,
    generate_short_id
)

def save_to_csv(website_data, filename="video_data.csv"):
    """Save data to common CSV file"""
    fieldnames = [
        'ID', 'Title', 'Channel Name', 'Video Type', 'Tags', 
        'Summary', 'Thumbnail URL', 'Original URL', 'Date Added'
    ]
    
    file_exists = os.path.exists(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(website_data)

def analyze_website(request):  # Renamed from generate_web_summary to match urls.py
    """Analyze website content and save to CSV"""
    website_url = request.GET.get('url')
    if not website_url:
        return JsonResponse(
            {"error": "No URL provided"}, 
            status=400  # Bad Request
        )

    scraped_data = scrape_website_content(website_url)
    if not scraped_data:
        return JsonResponse(
            {"error": "Failed to scrape website"}, 
            status=500  # Internal Server Error
        )

    try:
        summary = generate_summary(scraped_data['content'])
        tags = generate_tags(scraped_data['content'])

        website_data = {
            'ID': generate_short_id(),
            'Title': scraped_data['title'],
            'Channel Name': scraped_data['domain'],
            'Video Type': '',
            'Tags': ", ".join(tags),
            'Summary': summary,
            'Thumbnail URL': scraped_data['featured_image'],
            'Original URL': website_url,
            'Date Added': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        save_to_csv(website_data)
        return JsonResponse(website_data, status=200)  # OK

    except Exception as e:
        return JsonResponse(
            {"error": f"Error processing website: {str(e)}"}, 
            status=500  # Internal Server Error
        )