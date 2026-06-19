import os, sys
sys.path.insert(0, r'C:\Users\JLUIS\Music\ConectArte')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

# Simulate what settings.py does
from pathlib import Path
BASE_DIR = Path(r'C:\Users\JLUIS\Music\ConectArte\conectarte_project\settings.py').resolve().parent.parent
print(f'BASE_DIR = {BASE_DIR}')

env_path = BASE_DIR / '.env'
print(f'env_path = {env_path}')
print(f'exists = {env_path.exists()}')

from dotenv import load_dotenv
load_dotenv(env_path)

DEBUG = os.getenv('DEBUG', 'True') == 'True'
print(f'DEBUG = {DEBUG} (value from env: {repr(os.getenv("DEBUG"))})')
