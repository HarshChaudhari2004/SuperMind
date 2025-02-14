# video_summary/views.py
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime  # Add this import at the top
import logging

logger = logging.getLogger(__name__)

# Create a simple home view for the root URL
def home(request):
    return HttpResponse("Welcome to SuperMind! Use /api/generate-summary to interact with the API.")

import os
import requests
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import uuid
import csv
import string
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from dotenv import load_dotenv
from utils.supabase_client import save_to_supabase

load_dotenv()

# Function to convert a number to Base62 (shortened ID)
def to_base62(num):
    base62_chars = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    if num == 0:
        return base62_chars[0]
    base62_str = []
    while num > 0:
        base62_str.append(base62_chars[num % 62])
        num = num // 62
    return ''.join(reversed(base62_str))

# Function to generate a shorter ID using Base62 encoding
def generate_short_id():
    uuid_int = uuid.uuid4().int
    return to_base62(uuid_int)[:8]  # Shorten to the first 8 characters

# Set up Google Gemini API
API_KEY = os.getenv("api_key1")
# Use the API key with the GenAI configuration
genai.configure(api_key=API_KEY)


# Set up YouTube Data API
YOUTUBE_API_KEY = "AIzaSyCMAy4vjJ4nfGcKy-99WMoK5jwAmJswLVA"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/"

# Fetch YouTube video details function
def fetch_youtube_details(video_id):
    try:
        video_details_url = f"{YOUTUBE_API_URL}videos?part=snippet,contentDetails&id={video_id}&key={YOUTUBE_API_KEY}"
        video_details_response = requests.get(video_details_url)
        video_details = video_details_response.json()

        if "items" not in video_details:
            return None, None, None, None

        video_item = video_details["items"][0]
        title = video_item["snippet"]["title"]
        channel_name = video_item["snippet"].get("channelTitle", "")
        category_id = video_item["snippet"]["categoryId"]
        
        # Get HQ720 thumbnail with fallbacks
        thumbnails = video_item["snippet"]["thumbnails"]
        thumbnail_url = (
            thumbnails.get("maxres", {}).get("url") or  # Try maxres first
            f"https://i.ytimg.com/vi/{video_id}/hq720.jpg" or  # Try direct HQ720
            thumbnails.get("high", {}).get("url") or  # Fallback to high
            thumbnails.get("medium", {}).get("url") or  # Further fallback
            ""  # Empty if nothing found
        )

        category_url = f"{YOUTUBE_API_URL}videoCategories?part=snippet&id={category_id}&key={YOUTUBE_API_KEY}"
        category_response = requests.get(category_url)
        category_data = category_response.json()
        video_type = category_data["items"][0]["snippet"]["title"]

        return title, channel_name, video_type, thumbnail_url

    except Exception as e:
        print(f"Error fetching YouTube details: {e}")
        return None, None, None, None

# Function to extract transcript details from YouTube
def extract_transcript_details(youtube_video_url):
    try:
        # Improved URL parsing
        if 'youtu.be' in youtube_video_url:
            video_id = youtube_video_url.split('/')[-1].split('?')[0]
        else:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
            
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try manual transcripts first
        try:
            transcript = transcript_list.find_transcript(['en-IN', 'en', 'mr', 'hi'])
        except NoTranscriptFound:
            # Fallback to auto-generated transcripts
            try:
                transcript = transcript_list.find_manually_created_transcript()
            except:
                transcript = transcript_list.find_generated_transcript(['hi', 'en'])

        transcript_text = " ".join([entry["text"] for entry in transcript.fetch()])
        return transcript_text
    except NoTranscriptFound as e:
        logger.error(f"No transcript found for video {video_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error extracting transcript for video {video_id}: {str(e)}")
        return None

# Function to generate summary using Gemini
def generate_summary(content):
    try:
        if not content:
            return "No content available."
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(f"Summarize this text in maximum 7-8 lines:\n\n{content}")
        summary = response.text if hasattr(response, 'text') else 'Error generating summary.'
        return summary
    except Exception as e:
        return "Error generating summary."

# Function to generate tags using Gemini
def generate_tags(content):
    try:
        if not content:
            return []
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(f'''Generate 50 keywords/tags in English from this text Generate a list of 50 relevant tags based on the text. 
                                          don't say anything in start of response like "Sure, here is a list of 30 relevant tags for the video:" 
                                          or after response ends directly write tags and nothing else. 
                                          i want them in this format strictly: tag1, tag2, tag3, tag4....:\n\n{content}''')
        tags = response.text.split(",") if hasattr(response, 'text') else []
        return [tag.strip() for tag in tags if tag.strip()]
    except Exception as e:
        return []

# Function to save to CSV
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

# View for generating summary and tags
def generate_keywords_and_summary(request):
    try:
        url = request.GET.get('url')
        user_id = request.GET.get('user_id')
        
        if not url or not user_id:
            return JsonResponse({"error": "Missing URL or user_id"}, status=400)
        
        # Improved URL parsing
        try:
            if 'youtu.be' in url:
                video_id = url.split('/')[-1].split('?')[0]
            elif 'youtube.com' in url:
                if 'v=' in url:
                    video_id = url.split('v=')[1].split('&')[0]
                else:
                    video_id = url.split('/')[-1]
            else:
                return JsonResponse({"error": "Invalid YouTube URL format"}, status=400)
                
            if not video_id:
                return JsonResponse({"error": "Could not extract video ID"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"URL parsing failed: {str(e)}"}, status=400)

        logger.info(f"Processing YouTube URL: {url}")
        logger.info(f"Extracted video ID: {video_id}")
        
        try:
            title, channel_name, video_type, thumbnails = fetch_youtube_details(video_id)
            logger.info(f"Fetched video details: {title}")
        except Exception as e:
            logger.error(f"Error fetching YouTube details: {e}")
            return JsonResponse({"error": f"Failed to fetch video details: {str(e)}"}, status=500)

        if not (title and channel_name and video_type):
            return JsonResponse({"error": "Failed to get video information"}, status=500)

        try:
            transcript = extract_transcript_details(url)
            if not transcript:
                logger.error(f"No transcript available for video {video_id}")
                return JsonResponse({"error": "No transcript available for this video"}, status=400)
        except Exception as e:
            logger.error(f"Error extracting transcript: {e}")
            return JsonResponse({"error": "Failed to extract transcript"}, status=500)

        try:
            summary = generate_summary(transcript)
            tags = generate_tags(transcript)
        except Exception as e:
            print(f"Error generating summary/tags: {e}")
            return JsonResponse({"error": "Failed to generate summary"}, status=500)

        video_data = {
            'id': generate_short_id(),
            'user_id': user_id,
            'title': title,
            'channel_name': channel_name,
            'video_type': video_type,
            'tags': ", ".join(tags),
            'summary': summary,
            'thumbnail_url': thumbnails,
            'original_url': url,
            'date_added': datetime.now().isoformat()
        }

        # Save to Supabase
        try:
            result = save_to_supabase(video_data)
            if not result:
                return JsonResponse({"error": "Failed to save to database"}, status=500)
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return JsonResponse({"error": "Failed to save data"}, status=500)

        return JsonResponse(video_data)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({"error": str(e)}, status=500)