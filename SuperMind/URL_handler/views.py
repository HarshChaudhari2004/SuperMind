from django.http import JsonResponse
from .csv_operations import save_user_notes_to_csv, fetch_csv_data
import json

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
        # Fetch video data from 'video_data.csv'
        data = fetch_csv_data('video_data.csv')
        return JsonResponse(data, safe=False)  # Ensure safe=False for non-dict responses
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
