from django.http import JsonResponse
from .utils import download_instagram_post

def instagram_analysis_view(request):
    url = request.GET.get('url')
    if not url:
        return JsonResponse({"error": "No URL provided."}, status=400)

    result = download_instagram_post(url)
    return JsonResponse(result)
