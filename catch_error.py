import os, sys
sys.path.insert(0, r'C:\Users\JLUIS\Music\ConectArte')

from dotenv import load_dotenv
from pathlib import Path
BASE_DIR = Path(r'C:\Users\JLUIS\Music\ConectArte\conectarte_project\settings.py').resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

import django
django.setup()

from django.conf import settings
print(f"DEBUG = {settings.DEBUG}")

import logging
logging.basicConfig(level=logging.DEBUG)

from django.test import Client
c = Client()

# Try to catch the exact exception
import traceback
try:
    resp = c.get('/admin/login/')
    print(f"Status: {resp.status_code}")
    if resp.status_code == 500:
        print("Body:", resp.content)
except Exception as e:
    traceback.print_exc()
