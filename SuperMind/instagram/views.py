from django.http import JsonResponse
from .utils import download_instagram_post
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def instagram_analysis_view(request):
    try:
        url = request.GET.get('url')
        if not url:
            return JsonResponse({"error": "No URL provided."}, status=400)

        # Add user_id to the context
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return JsonResponse({"error": "User ID not found."}, status=401)

        result = download_instagram_post(url, user_id)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
