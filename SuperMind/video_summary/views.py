# video_summary/views.py
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime  # Add this import at the top

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
        video_id = youtube_video_url.split("v=")[1].split("&")[0]
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en-IN', 'en', 'mr', 'hi'])
        transcript_text = " ".join([entry["text"] for entry in transcript.fetch()])
        return transcript_text
    except NoTranscriptFound as e:
        return None
    except Exception as e:
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
    fieldnames = [
        'ID', 'Title', 'Channel Name', 'Video Type', 'Tags', 
        'Summary', 'Thumbnail URL', 'Original URL', 'Date Added'
    ]
    
    file_exists = os.path.exists(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(video_data)

# View for generating summary and tags
def generate_keywords_and_summary(request):
    youtube_video_url = request.GET.get('url')
    if youtube_video_url:
        video_id = youtube_video_url.split("v=")[1].split("&")[0]
        title, channel_name, video_type, thumbnails = fetch_youtube_details(video_id)
        if title and channel_name and video_type:
            transcript = extract_transcript_details(youtube_video_url)
            if transcript:
                summary = generate_summary(transcript)
                tags = generate_tags(transcript)
                video_data = {
                    'ID': generate_short_id(),
                    'Title': title,
                    'Channel Name': channel_name,
                    'Video Type': video_type,
                    'Tags': ", ".join(tags),
                    'Summary': summary,
                    'Thumbnail URL': thumbnails,
                    'Original URL': youtube_video_url,
                    'Date Added': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_to_csv(video_data)
                return JsonResponse(video_data, safe=False)
            else:
                return JsonResponse({"error": "Transcript not available."})
        else:
            return JsonResponse({"error": "Video details not found."})
    return JsonResponse({"error": "Invalid URL."})
