import instaloader
import requests
import re
import time
import google.generativeai as genai
import uuid
import string
import pandas as pd
import os
import csv  # Added import for csv

# Set up Google Gemini API
genai.configure(api_key="AIzaSyAs3_dAYF7KMlWJrpdyC9TbXMwsu73A_bg")

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

def download_instagram_post(url):
    L = instaloader.Instaloader()
    shortcode = extract_shortcode_from_url(url)
    if not shortcode:
        return {"error": "Invalid URL. Could not extract shortcode."}

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        return {"error": f"Error loading post: {e}"}

    if post.is_video:
        video_url = post.video_url
        download_video(video_url, shortcode)
        return analyze_video_with_ai(shortcode, post)
    else:
        return {"error": "The post does not contain a video."}

def extract_shortcode_from_url(url):
    pattern = r"instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+)"
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

def analyze_video_with_ai(shortcode, post):
    video_file_name = f"{shortcode}.mp4"
    video_file = genai.upload_file(path=video_file_name)
    while video_file.state.name == "PROCESSING":
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        return {"error": "Video processing failed"}

    prompt = '''Summarize this video content, and get the context of the video in a few lines. Write all of it in a few lines. 
    don't say anything in start of response like "Sure, here is the summary of the video content:" or at the end of response just write the summary and nothing else.'''
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

    response_summary = model.generate_content([video_file, prompt], request_options={"timeout": 600})
    summary_text = response_summary.text

    prompt_tags = '''Generate a list of 50 relevant tags in English based on the content of the video. 
    don't say anything in start of response like "Sure, here is a list of 30 relevant tags for the video:" or after response ends directly write tags and nothing else. 
    i want them in this format strictly: tag1, tag2, tag3, tag4....'''
    response_tags = model.generate_content([video_file, prompt_tags], request_options={"timeout": 600})
    tags_text = response_tags.text

    hashtags = extract_hashtags(post.caption) + extract_hashtags(summary_text)
    all_tags = tags_text.strip().replace('#', '') + "," + ",".join([hashtag.replace('#', '') for hashtag in hashtags])

    data = {
        'ID': generate_short_id(),
        'Title': post.caption if post.caption else "No Caption",
        'Channel Name': post.owner_username,
        'Tags': all_tags,
        'Summary': summary_text,
        'Thumbnail URL': post.url,
        'Original URL': f"https://www.instagram.com/p/{shortcode}/"
    }

    save_to_csv(data)

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

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

def save_to_csv(data, filename="video_data.csv"):  # Changed from instagram_video_data.csv
    from datetime import datetime
    
    fieldnames = [
        'ID', 'Title', 'Channel Name', 'Video Type', 'Tags', 
        'Summary', 'Thumbnail URL', 'Original URL', 'Date Added'
    ]

    data.update({
        'Video Type': 'Instagram',  # Add video type
        'Date Added': datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add date
    })

    file_exists = os.path.exists(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
