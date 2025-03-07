import os
from dotenv import load_dotenv
import requests
import re  # Add this import
import google.generativeai as genai
from bs4 import BeautifulSoup
import uuid
import string
from urllib.parse import unquote, urlparse
import csv
from datetime import datetime
import json
from typing import Dict, Optional, List

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
API_KEY = os.getenv("api_key2")
# Use the API key with the GenAI configuration
genai.configure(api_key=API_KEY)

def get_website_info(website_url, soup):
    try:
        title = soup.title.string if soup.title else ""
        domain = urlparse(website_url).netloc
        featured_image = ""
        og_image = soup.find("meta", property="og:image")
        if og_image:
            featured_image = og_image.get("content", "")
        else:
            first_image = soup.find("img")
            if (first_image):
                featured_image = first_image.get("src", "")
        return title.strip(), domain, featured_image
    except Exception as e:
        print(f"Error getting website info: {e}")
        return "", "", ""

def save_to_csv(website_data, filename="web_data.csv"):
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

# Function to fetch and scrape website content
def scrape_website_content(website_url):
    try:
        # Decode the URL if it has encoded parameters
        website_url = unquote(website_url)
        
        # Adding user-agent header to simulate a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(website_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Check for non-HTML content
        if 'text/html' not in response.headers.get('Content-Type', ''):
            raise ValueError("Non-HTML content received.")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get website information
        title, domain, featured_image = get_website_info(website_url, soup)
        
        paragraphs = soup.find_all('p')
        
        if not paragraphs:
            raise ValueError("No paragraphs found.")
        
        content = " ".join([para.get_text() for para in paragraphs])
        
        return {
            'content': content,
            'title': title,
            'domain': domain,
            'featured_image': featured_image
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except ValueError as e:
        print(f"Value error: {e}")
        return None
    except Exception as e:
        print(f"Error scraping website: {e}")
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
        print(f"Error generating summary with Gemini: {e}")
        return "Error generating summary."

# Function to generate tags using Gemini
def generate_tags(content):
    try:
        if not content:
            return []
        
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(f'''Generate 50 keywords/tags in English from this text Generate a list of 50 relevant tags based on the text. 
                                          don't say anything in start of response like "Sure, here is a list of 30 relevant tags for the video:" or after response ends directly write tags and nothing else. 
                                          i want them in this format strictly: tag1, tag2, tag3, tag4....:\n\n{content}''')
        tags = response.text.split(",") if hasattr(response, 'text') else []
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        return tags
    except Exception as e:
        print(f"Error generating tags with Gemini: {e}")
        return []

def clean_reddit_text(text: str) -> str:
    """Clean Reddit markdown and other formatting"""
    if not text:
        return ""
    # Remove markdown links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove markdown formatting
    text = re.sub(r'[*_~>`]', '', text)
    return text.strip()

def scrape_reddit_content(url: str) -> Optional[Dict]:
    """Scrape Reddit content from either frontend data or backend scraping"""
    # If frontend data is passed as a dict, use it directly
    if isinstance(url, dict):
        required_fields = ['content', 'title', 'domain', 'author', 'featured_image', 'post_type']
        if all(field in url for field in required_fields):
            return url
        else:
            print("Missing required fields in frontend data")
            return None

    # Handle short Reddit URLs (/r/subreddit/s/shortcode)
    if '/s/' in url:
        print(f"Detected Reddit short URL format: {url}")
        try:
            # First try to resolve the short URL to get the full URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Get the final URL after redirects
            resolved_url = response.url
            print(f"Short URL resolved to: {resolved_url}")
            
            # If we got redirected to a comments page, use that URL instead
            if '/comments/' in resolved_url:
                url = resolved_url
                print(f"Using resolved URL for scraping: {url}")
            else:
                # If we can't resolve to a comments URL, extract post info from the page
                soup = BeautifulSoup(response.text, 'html.parser')
                # Try to find a link to the full comments page
                comments_link = soup.select_one('a[data-testid="post-title"]')
                if comments_link and comments_link.get('href'):
                    post_path = comments_link.get('href')
                    if post_path.startswith('/'):
                        url = f"https://www.reddit.com{post_path}"
                        print(f"Found comments link: {url}")
                    else:
                        url = post_path
                        print(f"Found external link: {url}")
        except Exception as e:
            print(f"Error resolving short Reddit URL: {e}")
            # Continue with the original URL as fallback
    
    # Enhanced URL cleaning logic before fetching JSON
    try:
        # Remove query parameters and trailing slash
        parsed_url = urlparse(url)
        base_path = parsed_url.path.rstrip('/')  # Remove trailing slash
        clean_url = f"https://www.reddit.com{base_path}"  # Use only the path
        json_url = f"{clean_url}.json"
        
        print(f"Cleaned URL: {clean_url}")
        print(f"Fetching Reddit JSON from: {json_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Get both JSON and HTML responses using original URL for HTML
        json_response = requests.get(json_url, headers=headers, timeout=10)
        html_response = requests.get(url, headers=headers, timeout=10)  # Keep original URL for HTML
        
        json_response.raise_for_status()
        html_response.raise_for_status()
        
        # Check if we got valid JSON data
        try:
            data = json_response.json()
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from Reddit: {str(e)}")
            print(f"First 100 characters of response: {json_response.text[:100]}")
            return None
        
        if not isinstance(data, list) or len(data) < 2:
            return None
            
        post_data = data[0]['data']['children'][0]['data']
        comments_data = data[1]['data']['children']
        
        # Parse HTML to get subreddit icon
        soup = BeautifulSoup(html_response.text, 'html.parser')
        
        # Get post content
        title = post_data.get('title', '')
        selftext = clean_reddit_text(post_data.get('selftext', ''))
        subreddit = post_data.get('subreddit', '')
        author = post_data.get('author', '[deleted]')
        
        # Enhanced thumbnail logic
        thumbnail = ''
        is_video_post = post_data.get('is_video', False)  # Check if it's a video post
        
        # 1. First try url_overridden_by_dest for direct image posts (not videos)
        if not is_video_post and post_data.get('url_overridden_by_dest'):
            url_override = post_data['url_overridden_by_dest']
            if any(url_override.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                thumbnail = url_override

        # 2. If it's a video post, skip other image checks and go straight for subreddit icon
        if is_video_post:
            subreddit_icon = soup.select_one('.shreddit-subreddit-icon__icon')
            if subreddit_icon and subreddit_icon.get('src'):
                thumbnail = subreddit_icon['src']
            else:
                # Try alternative selector for community icon
                community_icon = soup.select_one('img[alt$="icon"]')
                if community_icon and community_icon.get('src'):
                    thumbnail = community_icon['src']
        else:
            # 3. Try thumbnail field if it's not "default" or "self"
            if not thumbnail and post_data.get('thumbnail'):
                if post_data['thumbnail'] not in ['default', 'self', 'nsfw']:
                    thumbnail = post_data['thumbnail']

            # 4. Try preview images as fallback
            if not thumbnail and post_data.get('preview', {}).get('images'):
                preview = post_data['preview']['images'][0]
                if preview.get('source', {}).get('url'):
                    thumbnail = preview['source']['url'].replace('&amp;', '&')

            # 5. Try to get subreddit icon as last resort for non-video posts
            if not thumbnail:
                subreddit_icon = soup.select_one('.shreddit-subreddit-icon__icon')
                if subreddit_icon and subreddit_icon.get('src'):
                    thumbnail = subreddit_icon['src']
                else:
                    community_icon = soup.select_one('img[alt$="icon"]')
                    if community_icon and community_icon.get('src'):
                        thumbnail = community_icon['src']

        # Clean the thumbnail URL if it exists
        if thumbnail:
            # Remove escaped HTML entities and query parameters
            thumbnail = thumbnail.replace('&amp;', '&').split('?')[0]
            
        # Combine content for analysis
        full_content = f"Title: {title}\n\nPost Content: {selftext}\n\n"
        if comments_data:
            top_comments = []
            comment_count = 0
            
            # Loop through comments to get non-stickied ones
            for comment in comments_data:
                if comment_count >= 15:  # Increase number of comments to 15
                    break
                    
                comment_data = comment.get('data', {})
                if (
                    'body' in comment_data 
                    and not comment_data.get('stickied', False)  # Skip stickied comments
                ):
                    comment_text = clean_reddit_text(comment_data['body'])
                    if comment_text and len(comment_text) > 20:  # Keep minimum length requirement
                        top_comments.append(comment_text)
                        comment_count += 1
                        
            if top_comments:
                full_content += "Top Comments:\n" + "\n".join(f"- {comment}" for comment in top_comments)
        
        return {
            'content': full_content,
            'title': title,
            'domain': f"r/{subreddit}",
            'author': author,
            'featured_image': thumbnail,
            'post_type': 'reddit_post'
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Reddit request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Reddit JSON error: {e}")
        return None
    except Exception as e:
        print(f"Error scraping Reddit: {e}")
        return None
