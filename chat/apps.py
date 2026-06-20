from django.apps import AppConfig
from django.core.management import call_command
import os

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        # Ejecutar migraciones solo si estamos en Render (donde existe DATABASE_URL)
        if os.environ.get('DATABASE_URL'):
            try:
                call_command('migrate')
                print("Migraciones ejecutadas automáticamente.")
            except Exception as e:
                print(f"Error en migraciones: {e}")