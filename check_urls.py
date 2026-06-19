import os, sys, django
sys.path.insert(0, r'C:\Users\JLUIS\Music\ConectArte')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

django.setup()

from django.test import RequestFactory
from django.urls import resolve

try:
    match = resolve('/admin/login/')
    print(f"Resolved: {match.url_name}, view: {match.func}")
except Exception as e:
    print(f"Resolve error: {e}")
