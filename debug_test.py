import os, sys, django
from pathlib import Path

BASE_DIR = Path(r'C:\Users\JLUIS\Music\ConectArte\conectarte_project\settings.py').resolve().parent.parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env', override=True)

django.setup()
from django.conf import settings
print(f"DEBUG = {settings.DEBUG}")
print(f"SECRET_KEY starts with: {settings.SECRET_KEY[:20]}...")

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('django.request')

from django.test import Client
c = Client()
resp = c.get('/admin/login/')
print(f"\n/admin/login/ -> Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Body snippet: {resp.content[:500]}")
