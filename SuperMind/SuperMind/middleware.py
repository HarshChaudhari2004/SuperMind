import os
import supabase
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

# Initialize Supabase Client
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

class SupabaseAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            try:
                user = supabase_client.auth.get_user(token)
                if user and user.user:
                    request.user_id = user.user.id  # Set user_id on request
                    return None
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=401)
        return JsonResponse({"error": "Authentication required"}, status=401)
