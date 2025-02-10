from supabase import create_client
from django.conf import settings
from datetime import datetime

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def save_to_supabase(content_data):
    """Save content data to Supabase"""
    try:
        if not content_data.get('user_id'):
            raise ValueError("user_id is required")

        # Format date if needed
        if 'date_added' in content_data:
            content_data['date_added'] = datetime.now().isoformat()

        result = supabase.table('content').insert(content_data).execute()
        
        if hasattr(result, 'error') and result.error:
            raise Exception(result.error.message)
            
        return result.data[0] if result.data else None

    except Exception as e:
        print(f"Error saving to Supabase: {e}")
        return None
