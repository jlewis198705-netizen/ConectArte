import os, sys
sys.path.insert(0, r'C:\Users\JLUIS\Music\ConectArte')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

from django.conf import settings
print(f"DEBUG = {settings.DEBUG}")
print(f"ALLOWED_HOSTS = {settings.ALLOWED_HOSTS}")
print(f"INSTALLED_APPS = {settings.INSTALLED_APPS}")

try:
    from django.contrib.admin import site
    print("Admin site loaded OK")
    for model, admin_class in site._registry.items():
        print(f"  Registered: {model.__name__}")
except Exception as e:
    print(f"Admin error: {e}")
