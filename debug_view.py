"""Quick debug view - add to chat/views.py temporarily"""
from django.http import HttpResponse
from django.conf import settings

def debug_info(request):
    import os
    lines = [
        f"DEBUG = {settings.DEBUG}",
        f"SECRET_KEY = {settings.SECRET_KEY[:30]}...",
        f"os.getenv('DEBUG') = {os.getenv('DEBUG')}",
        f"os.getenv('SECRET_KEY') = {os.getenv('SECRET_KEY', 'NOT SET')[:30]}...",
        f"BASE_DIR = {settings.BASE_DIR}",
        f".env exists = {os.path.exists(os.path.join(settings.BASE_DIR, '.env'))}",
    ]
    return HttpResponse('<br>'.join(lines))
