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
        # Skip auth for OPTIONS requests
        if request.method == 'OPTIONS':
            return None
            
        # Allow access to these endpoints without authentication
        exempt_paths = [
            '/get-csrf-token/',
            '/web/get-csrf-token/',
            '/api/test/',
            '/admin/',
            '/',  # Home page
        ]
        
        # Check if current path is exempt
        for path in exempt_paths:
            if request.path.startswith(path):
                return None
                
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            try:
                user = supabase_client.auth.get_user(token)
                if user and user.user:
                    request.user_id = user.user.id  # Set user_id on request
                    return None
            except Exception as e:
                print(f"Auth error: {e}")
                return JsonResponse({"error": "Invalid authentication token"}, status=401)
        return JsonResponse({"error": "Authentication required"}, status=401)
