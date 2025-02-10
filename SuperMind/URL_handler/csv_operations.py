import csv
import os
import uuid
import string
from django.http import JsonResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to convert a number to Base62 (shortened ID)
def to_base62(num):
    base62_chars = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    if num == 0:
        return base62_chars[0]
    base62_str = []
    while num > 0:
        base62_str.append(base62_chars[num % 62])
        num //= 62
    return ''.join(reversed(base62_str))

# Function to generate a shorter ID using Base62 encoding
def generate_short_id():
    uuid_int = uuid.uuid4().int
    return to_base62(uuid_int)[:8]  # Shorten to the first 8 characters

# Function to save user notes and URL to CSV
def save_user_notes_to_csv(original_url, user_notes, user_id, filename="video_data.csv"):
    try:
        # Absolute path to the video_data.csv file
        file_path = r"I:\SuperMind\SuperMind\video_data.csv"  # Update this with the correct path

        # Prepare the data for CSV
        website_data = {
            'ID': generate_short_id(),
            'user_id': user_id,  # Add user_id to the data
            'Title': original_url,
            'Description': user_notes or "User added notes",
            'Channel Name': "N/A",
            'Thumbnail URL': "N/A",
            'Video Type': "N/A",
            'Top 100 Comments': "N/A",
            'Tags': "N/A",
            'Summary': "N/A",
            'Original URL': original_url,
            'User notes': user_notes,
        }

        # Check if the file exists
        file_exists = os.path.exists(file_path)
        
        # Open the file in append mode
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            fieldnames = [
                'ID', 'user_id', 'Title', 'Description', 'Channel Name', 
                'Thumbnail URL', 'Video Type', 'Top 100 Comments', 'Tags', 
                'Summary', 'Original URL', 'User notes'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # If the file does not exist, write the header
            if not file_exists:
                writer.writeheader()
            
            # Write the new row to the CSV
            writer.writerow(website_data)

        return {"message": "User notes saved successfully!"}
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        return {"error": str(e)}

# Function to fetch CSV data and return as JSON response
def fetch_csv_data(filename):
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        data = list(reader)
        print("CSV Data:", data)  # Add debug logging
        return data

# Function to fetch data from both CSV files and return a combined response
def fetch_combined_csv_data(request):
    # Path to both CSV files
    video_data_path = r"I:\SuperMind\SuperMind\video_data.csv"  # Path for video_data.csv
    instagram_data_path = r"I:\SuperMind\SuperMind\instagram_video_data.csv"  # Path for instagram_video_data.csv
    
    video_data = fetch_csv_data(video_data_path)  # Fetch data from video_data.csv
    instagram_data = fetch_csv_data(instagram_data_path)  # Fetch data from instagram_video_data.csv

    # Combine both datasets
    combined_data = video_data + instagram_data

    # Return the combined data as JSON
    return JsonResponse(combined_data, safe=False)

