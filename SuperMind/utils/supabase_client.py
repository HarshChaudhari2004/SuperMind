from supabase import create_client
from django.conf import settings
from datetime import datetime

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def save_to_supabase(content_data):
    """Save content data to Supabase"""
    try:
        # Ensure the date is in the correct format
        if 'date_added' in content_data:
            # Convert to ISO format if it's not already
            if isinstance(content_data['date_added'], str):
                try:
                    datetime.strptime(content_data['date_added'], "%Y-%m-%d %H:%M:%S")
                    content_data['date_added'] = datetime.now().isoformat()
                except ValueError:
                    pass
            else:
                content_data['date_added'] = datetime.now().isoformat()
                
        # Convert ID field if needed
        if 'ID' in content_data:
            content_data['id'] = content_data.pop('ID')

        result = supabase.table('content').insert(content_data).execute()
        return result
    except Exception as e:
        print(f"Error saving to Supabase: {e}")
        return None
