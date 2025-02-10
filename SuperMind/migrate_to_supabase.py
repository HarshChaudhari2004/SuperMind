import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

load_dotenv()

# Supabase setup
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

TEMPORARY_USER_ID = "8e8f73a9-7ad3-449c-b06f-e588bdabc635"

def convert_date_format(date_str):
    """Convert various date formats to ISO format"""
    try:
        # Try different date formats
        for fmt in [
            "%d-%m-%Y %H:%M",    # 31-01-2025 19:11
            "%Y-%m-%d %H:%M:%S",  # 2025-01-31 19:11:00
            "%Y-%m-%d %H:%M:%S.%f",  # 2025-01-31 19:11:00.000
            "%Y-%m-%dT%H:%M:%S.%fZ",  # 2025-01-31T19:11:00.000Z
        ]:
            try:
                return datetime.strptime(date_str, fmt).isoformat()
            except ValueError:
                continue
        # If no format matches, return current time
        return datetime.now().isoformat()
    except Exception as e:
        print(f"Error converting date {date_str}: {e}")
        return datetime.now().isoformat()

def migrate_csv_to_supabase(csv_path):
    """Migrate data from CSV to Supabase"""
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Transform data to match Supabase schema
                date_added = convert_date_format(row.get('Date Added', ''))
                
                content_data = {
                    'id': row.get('ID', ''),
                    'user_id': TEMPORARY_USER_ID,
                    'title': row.get('Title', ''),
                    'channel_name': row.get('Channel Name', ''),
                    'video_type': row.get('Video Type', ''),
                    'tags': row.get('Tags', ''),
                    'summary': row.get('Summary', ''),
                    'thumbnail_url': row.get('Thumbnail URL', ''),
                    'original_url': row.get('Original URL', ''),
                    'date_added': date_added
                }
                
                # Insert into Supabase
                try:
                    result = supabase.table('content').insert(content_data).execute()
                    print(f"Migrated content: {content_data['id']}")
                except Exception as e:
                    print(f"Error migrating content {content_data['id']}: {e}")
                    continue

    except Exception as e:
        print(f"Error reading CSV file: {e}")

def main():
    # Define paths to your CSV files
    base_dir = Path(__file__).resolve().parent
    csv_files = [
        base_dir / 'video_data.csv',
        # Add other CSV files if needed
    ]

    for csv_file in csv_files:
        if csv_file.exists():
            print(f"Migrating {csv_file}...")
            migrate_csv_to_supabase(csv_file)
        else:
            print(f"File not found: {csv_file}")

if __name__ == "__main__":
    main()
