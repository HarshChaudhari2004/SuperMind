import os
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
import uuid
import string
from urllib.parse import unquote, urlparse
import csv
from datetime import datetime

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
genai.configure(api_key="AIzaSyBEfuoZbcieg3a7JnzE0LSgiLfmeIBg8q0")  # Ensure API key is set in your environment

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
