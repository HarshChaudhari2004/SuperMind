import instaloader
import re
from supabase import create_client
import time
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Instaloader
L = instaloader.Instaloader()

def extract_shortcode_from_url(url):
    """Extract the shortcode from an Instagram URL."""
    pattern = r"instagram\.com/(?:reel|p|reels)/([A-Za-z0-9_-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_fresh_thumbnail_url(shortcode):
    """Get a fresh thumbnail URL for an Instagram post."""
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        return post.url
    except Exception as e:
        logger.error(f"Error fetching thumbnail for shortcode {shortcode}: {e}")
        return None

def update_instagram_thumbnails():
    """Update thumbnail URLs for all Instagram content in the database."""
    try:
        # Fetch all content where original_url contains 'instagram.com'
        response = supabase.table('content')\
            .select('id, original_url, thumbnail_url')\
            .ilike('original_url', '%instagram.com%')\
            .execute()
        
        if not response.data:
            logger.info("No Instagram content found in database")
            return

        updated_count = 0
        failed_count = 0

        for item in response.data:
            try:
                shortcode = extract_shortcode_from_url(item['original_url'])
                if not shortcode:
                    logger.warning(f"Could not extract shortcode from URL: {item['original_url']}")
                    continue

                new_thumbnail_url = get_fresh_thumbnail_url(shortcode)
                if not new_thumbnail_url:
                    logger.warning(f"Could not get new thumbnail URL for shortcode: {shortcode}")
                    failed_count += 1
                    continue

                # Update the thumbnail_url field
                update_response = supabase.table('content')\
                    .update({'thumbnail_url': new_thumbnail_url})\
                    .eq('id', item['id'])\
                    .execute()

                if update_response.data:
                    updated_count += 1
                    logger.info(f"Updated thumbnail for content ID: {item['id']}")
                
                # Add a small delay to avoid rate limiting
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error processing content ID {item['id']}: {e}")
                failed_count += 1

        logger.info(f"Update complete. Successfully updated: {updated_count}, Failed: {failed_count}")

    except Exception as e:
        logger.error(f"Error in update_instagram_thumbnails: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting Instagram thumbnail update process...")
    update_instagram_thumbnails()
    logger.info("Finished Instagram thumbnail update process")
