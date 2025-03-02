from django.http import JsonResponse
from .utils import download_instagram_post
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def instagram_analysis_view(request):
    try:
        url = request.GET.get('url')
        user_id = request.GET.get('user_id')  # Get user_id from query parameters
        
        if not url:
            return JsonResponse({"error": "No URL provided."}, status=400)
            
        if not user_id:
            return JsonResponse({"error": "User ID required."}, status=400)

        result = download_instagram_post(url, user_id)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
