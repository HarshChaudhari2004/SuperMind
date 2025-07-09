import instaloader
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime  # Add this import at the top
from utils.supabase_client import save_to_supabase
import requests
import re
import time
import google.generativeai as genai
import uuid
import string
# import pandas as pd
import os
from dotenv import load_dotenv
import csv  # Added import for csv
from datetime import datetime
from utils.supabase_client import save_to_supabase
import glob

#setup gemini api key
load_dotenv()
API_KEY = os.getenv("api_key2")
# Use the API key with the GenAI configuration
genai.configure(api_key=API_KEY)

def to_base62(num):
    base62_chars = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    if num == 0:
        return base62_chars[0]
    base62_str = []
    while num > 0:
        base62_str.append(base62_chars[num % 62])
        num = num // 62
    return ''.join(reversed(base62_str))

def generate_short_id():
    uuid_int = uuid.uuid4().int
    return to_base62(uuid_int)[:8]

def download_instagram_post(url, user_id):
    """Handle both reels and image posts"""
    L = instaloader.Instaloader()
    shortcode = extract_shortcode_from_url(url)
    if not shortcode:
        return {"error": "Invalid URL. Could not extract shortcode."}

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # For video posts (reels)
        if post.is_video:
            video_url = post.video_url
            return process_video_content(video_url, shortcode, post, user_id)
        
        # For image posts (single or carousel)
        else:
            return process_image_content(post, user_id)
            
    except Exception as e:
        return {"error": f"Error loading post: {e}"}

def extract_shortcode_from_url(url):
    # Updated pattern to match both reels and posts
    pattern = r"instagram\.com/(?:p|reels|reel)/([A-Za-z0-9_-]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def download_video(url, shortcode):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        file_path = f"{shortcode}.mp4"
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        return file_path
    else:
        return {"error": "Failed to retrieve video."}

def analyze_video_with_ai(shortcode, post, user_id):
    """Updated to include user_id parameter"""
    video_file_name = f"{shortcode}.mp4"
    video_file = genai.upload_file(path=video_file_name)
    while video_file.state.name == "PROCESSING":
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        return {"error": "Video processing failed"}

    video_summary_prompt = '''Summarize this video content, and get the context of the video in a few lines. Write all of it in a few lines. 
    don't say anything in start of response like "Sure, here is the summary of the video content:" or at the end of response just write the summary and nothing else.'''
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    response_summary = model.generate_content([video_file, video_summary_prompt], request_options={"timeout": 600})
    summary_text = response_summary.text

    video_tags_prompt = '''Generate a list of 50 relevant tags in English based on the content of the video. 
    don't say anything in start of response like "Sure, here is a list of 30 relevant tags for the video:" or after response ends directly write tags and nothing else. 
    i want them in this format strictly: tag1, tag2, tag3, tag4....'''
    response_tags = model.generate_content([video_file, video_tags_prompt], request_options={"timeout": 600})
    tags_text = response_tags.text

    hashtags = extract_hashtags(post.caption) + extract_hashtags(summary_text)
    all_tags = tags_text.strip().replace('#', '') + "," + ",".join([hashtag.replace('#', '') for hashtag in hashtags])
    import requests
    data = {
        'id': generate_short_id(),
        'user_id': user_id,
        'title': post.caption if post.caption else "No Caption",
        'channel_name': post.owner_username,
        'video_type': 'instagram',
        'tags': all_tags,
        'summary': summary_text,
        'thumbnail_url': post.url,
        'original_url': f"https://www.instagram.com/p/{shortcode}/",
        'date_added': datetime.now().isoformat()
    }

    # Save to both CSV and Supabase
    save_to_csv(data)
    save_to_supabase(data)

    try:
        video_file.delete()
    except Exception as e:
        return {"error": f"Error deleting Gemini file: {e}"}

    try:
        if os.path.exists(video_file_name):
            os.remove(video_file_name)
    except Exception as e:
        return {"error": f"Error deleting local video file: {e}"}

    return data

def process_video_content(video_url, shortcode, post, user_id):
    """Process Instagram video content"""
    file_path = download_video(video_url, shortcode)
    if isinstance(file_path, dict) and 'error' in file_path:
        return file_path
    
    result = analyze_video_with_ai(shortcode, post, user_id)
    
    # Cleanup video file
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error removing video file: {e}")
        
    return result

def process_image_content(post, user_id):
    """Process single images or carousel posts with optimized cleanup"""
    temp_files = []
    images = []
    try:
        # Initialize Gemini
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        # Handle carousel posts
        if post.mediacount > 1:
            # Extract img_index from URL if present
            post_url = f"https://www.instagram.com/p/{post.shortcode}/"
            img_index = 1  # Default to first image
            if "img_index=" in post_url:
                try:
                    img_index = int(post_url.split("img_index=")[1].split("&")[0])
                except (ValueError, IndexError):
                    img_index = 1

            # Get all sidecar nodes
            sidecar_nodes = list(post.get_sidecar_nodes())
            total_images = len(sidecar_nodes)
            
            # Calculate which 3 images to process
            indices_to_process = []
            
            # Always include the first image (thumbnail)
            indices_to_process.append(0)
            
            if img_index > 1:
                # For images not at the start, get surrounding images
                prev_index = img_index - 2  # -2 because indices are 0-based
                next_index = img_index - 1  # Current image
                
                # Add indices while maintaining order and staying within bounds
                for idx in sorted(set([prev_index, next_index])):
                    if idx >= 0 and idx < total_images and idx not in indices_to_process:
                        indices_to_process.append(idx)
            else:
                # If starting from beginning, take first 2 images after the thumbnail
                indices_to_process.extend([i for i in range(1, min(3, total_images))])
            
            # Ensure we only process 3 images maximum
            indices_to_process = indices_to_process[:3]
            
            # Download selected images
            for i in indices_to_process:
                node = sidecar_nodes[i]
                image_url = node.display_url
                temp_file = f"temp_{i}.jpg"
                temp_files.append(temp_file)
                image_data = download_image(image_url, temp_file)
                images.append(image_data)
            
            # Process all images together with a single prompt
            carousel_prompt = '''Analyze these instagram post images together and provide a concise summary that:
            1. Describes the main themes or subjects across the images
            2. Notes any progression or connection between them
            3. Highlights key visual elements or details
            4. Any visible text or notable details.
            Keep the response focused and avoid analyzing each image separately.
            include any contextual clues that help understand the scene or message conveyed, but keep the response concise and under 100-150 words.'''
            
            # Pass all images to Gemini at once
            image_response = model.generate_content([*images, carousel_prompt])
            combined_content = image_response.text
            
        else:
            # Handle single image - existing code remains unchanged
            image_url = post.url
            temp_file = "temp_single.jpg"
            temp_files.append(temp_file)
            image_data = download_image(image_url, temp_file)
            images.append(image_data)
            
            # Analyze single image with optimized prompt
            single_image_prompt = '''Analyze this instagram post image and provide a brief summary covering:
                        1. The main subject or focus of the image.
                        2. Key visual elements, including colors, objects, and composition.
                        3. Any visible text or notable details.
                        Please include any contextual clues that help understand the scene or message conveyed, but keep the response concise and under 100-150 words.'''
            
            image_response = model.generate_content([image_data, single_image_prompt])
            combined_content = image_response.text

        # Generate focused tags
        image_tags_prompt = '''Generate a list of 43+ relevant tags in English based on the content of the image. 
    don't say anything in start of response like "Sure, here is a list of relevant tags for the video:" or after response ends directly write tags and nothing else. 
    i want them in this format strictly: tag1, tag2, tag3, tag4....'''
        tags_response = model.generate_content([combined_content, image_tags_prompt])
        tags = tags_response.text.strip()

        # Prepare data for storage - Remove optional fields
        data = {
            'id': generate_short_id(),
            'user_id': user_id,
            'title': post.caption if post.caption else "No Caption",
            'channel_name': post.owner_username,
            'video_type': 'instagram_image',
            'tags': tags,
            'summary': combined_content,
            'thumbnail_url': post.url,
            'original_url': f"https://www.instagram.com/p/{post.shortcode}/",
            'date_added': datetime.now().isoformat()
        }

        # Save to both CSV and Supabase
        save_to_csv(data)
        save_to_supabase(data)

        return data

    except Exception as e:
        return {"error": f"Error processing image content: {e}"}
    
    finally:
        # Clean up all temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error removing temporary file {temp_file}: {e}")
                
        # Also cleanup any processed files in Gemini
        try:
            for image_data in images:
                image_data.delete()
        except Exception as e:
            print(f"Error cleaning up Gemini files: {e}")

def download_image(url, filename):
    """Download image and return file object for Gemini"""
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return genai.upload_file(path=filename)
    else:
        raise Exception("Failed to download image")

def cleanup_temp_files():
    """Clean up temporary image files"""
    for file in glob.glob("temp_*.jpg"):
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error removing temporary file {file}: {e}")

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

def save_to_csv(video_data, filename="video_data.csv"):
    """Save data to CSV file"""
    # Remove is_carousel and media_count before saving to CSV
    data_to_save = {
        'id': video_data['id'],
        'user_id': video_data['user_id'],
        'title': video_data['title'],
        'channel_name': video_data['channel_name'],
        'video_type': video_data['video_type'],
        'tags': video_data['tags'],
        'summary': video_data['summary'],
        'thumbnail_url': video_data['thumbnail_url'],
        'original_url': video_data['original_url'],
        'date_added': video_data['date_added']
    }

    fieldnames = [
        'id', 'user_id', 'title', 'channel_name', 'video_type',
        'tags', 'summary', 'thumbnail_url', 'original_url', 'date_added'
    ]
    
    file_exists = os.path.exists(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_to_save)
