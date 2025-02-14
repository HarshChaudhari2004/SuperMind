import instaloader
import csv
import re

# Initialize Instaloader
L = instaloader.Instaloader()

def extract_shortcode_from_url(url):
    """Extract the shortcode from an Instagram URL."""
    pattern = r"instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def get_thumbnail_url(shortcode):
    """Retrieve the thumbnail URL for the given Instagram post."""
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        # For videos, this will return the video thumbnail URL. For photos, it will return the photo URL.
        return post.url
    except Exception as e:
        print(f"Error fetching post {shortcode}: {e}")
        return None

def update_thumbnail_url_in_csv(csv_filename="video_data.csv"):
    """Update only the Thumbnail URL in the CSV file where the Original URL is from Instagram."""
    rows = []

    # Read the existing CSV file
    with open(csv_filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)

    # Update the "Thumbnail URL" for each row where the "Original URL" is from Instagram
    for row in rows:
        if "instagram.com" in row['Original URL']:
            shortcode = extract_shortcode_from_url(row['Original URL'])
            if shortcode:
                new_thumbnail_url = get_thumbnail_url(shortcode)
                if new_thumbnail_url:
                    row['Thumbnail URL'] = new_thumbnail_url  # Update only the Thumbnail URL

    # Write the updated rows back to the CSV
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['id', 'user_id', 'title', 'channel_name', 'video_type', 'tags', 'summary', 'thumbnail_url', 'original_url', 'date_added']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# Example usage
update_thumbnail_url_in_csv()
