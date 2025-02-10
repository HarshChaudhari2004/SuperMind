from django.http import JsonResponse
from django.conf import settings
import supabase
from datetime import datetime
from .csv_operations import save_user_notes_to_csv, fetch_csv_data
import json

# Initialize Supabase client
supabase_client = supabase.create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# View to handle saving user notes and original URL to the CSV
def save_user_notes(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            original_url = data.get("originalUrl")
            user_notes = data.get("userNotes")

            # Call the function to save the data to CSV
            result = save_user_notes_to_csv(original_url, user_notes)

            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# View to get video data
def get_video_data(request):
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({"error": "user_id is required"}, status=400)

        # Fetch data from Supabase 'content' table
        response = supabase_client.table('content')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()

        if hasattr(response, 'data'):
            return JsonResponse(response.data, safe=False)
        else:
            return JsonResponse([], safe=False)

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
