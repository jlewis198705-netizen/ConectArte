import os, sys
from pathlib import Path

BASE_DIR = Path(r'C:\Users\JLUIS\Music\ConectArte\conectarte_project\settings.py').resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env', override=True)

# IMPORTANT: override=True ensures .env values override existing env

import django
django.setup()

from django.test import Client
c = Client()
resp = c.get('/admin/login/')
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    print('ADMIN OK')
else:
    print(f'ERROR: {resp.content[:500]}')
