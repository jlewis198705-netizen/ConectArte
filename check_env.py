import os, sys
sys.path.insert(0, r'C:\Users\JLUIS\Music\ConectArte')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conectarte_project.settings')

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
print(f'Looking for .env at: {env_path}')
print(f'File exists: {env_path.exists()}')

result = load_dotenv(env_path)
print(f'load_dotenv result: {result}')

print(f'DEBUG from env: {os.getenv("DEBUG")}')
print(f'SECRET_KEY from env: {os.getenv("SECRET_KEY")}')
