import os, sys
sys.path.insert(0, r'C:\Users\JLUIS\Music\ConectArte')

from dotenv import load_dotenv
from pathlib import Path
BASE_DIR = Path(r'C:\Users\JLUIS\Music\ConectArte\conectarte_project\settings.py').resolve().parent.parent
# Exactly like settings.py does - no override
load_dotenv(BASE_DIR / '.env')

print(f"DEBUG env = {repr(os.getenv('DEBUG'))}")
print(f"SECRET_KEY env = {'SET' if os.getenv('SECRET_KEY') else 'NOT SET'}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

import django
django.setup()

from django.conf import settings
print(f"settings.DEBUG = {settings.DEBUG}")

from django.test import Client
c = Client()
resp = c.get('/admin/login/')
print(f"Status: {resp.status_code}")
