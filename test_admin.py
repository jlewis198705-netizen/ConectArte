import os
import sys

sys.path.insert(0, r'C:\Users\JLUIS\Music\ConectArte')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

os.environ['SECRET_KEY'] = 'mm0M9le7n4gOfDSrFpyKwDtM2xPhfvxnt6BAovPLj6EGsvCuTHfhJBBZynu1-jxnrBk'
os.environ['DEBUG'] = 'True'

import django
django.setup()

from django.test import Client
c = Client()
resp = c.get('/admin/login/')
print(f'Status: {resp.status_code}')
print(f'Headers: {dict(resp.headers)}')
body_preview = resp.content[:500]
print(f'Body preview: {body_preview}')

if resp.status_code == 500:
    import traceback
    try:
        resp.render()
    except Exception as e:
        traceback.print_exc()
