# ConectArte

Marketplace de servicios artísticos. Conecta clientes con artistas visuales (muralistas, restauradores, ilustradores) a través de un sistema de chat en vivo, asignación inteligente por balanceo de carga, panel de administración personalizado y moderación de contenido.

## Tech Stack

- **Backend:** Django 6.0, Python 3.12
- **Base de datos:** PostgreSQL (producción) / SQLite (desarrollo local)
- **Frontend:** Tailwind CSS, Vanilla JS
- **Servidor:** Gunicorn + Whitenoise
- **Deploy:** Render

## Features

- **Roles:** Cliente, Artista y Administrador con permisos diferenciados
- **Solicitudes:** Clientes crean solicitudes de servicios artísticos
- **Asignación inteligente:** Algoritmo de balanceo de carga + round-robin que asigna automáticamente la solicitud al artista con menor carga laboral
- **Chat en vivo:** Sistema de mensajería con polling, imágenes de antes/después/progreso, y notificaciones de sistema
- **Panel admin:** Interfaz personalizada (sin Django Admin) con revisión de contenido, aprobación de imágenes, moderación de mensajes (soft-delete), y gestión de solicitudes
- **Estilo vintage:** Diseño responsivo con tema claro/oscuro
- **Preparado para producción:** Configuración para deploy en Render con PostgreSQL y almacenamiento estático optimizado

## Requisitos

- Python 3.12+
- pip

## Instalación local

```bash
# Clonar el repositorio
git clone https://github.com/jlewis198705-netizen/ConectArte.git
cd ConectArte

# Crear y activar entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor de desarrollo
python manage.py runserver
```

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `SECRET_KEY` | Clave secreta de Django | — |
| `DEBUG` | Modo debug | `True` |
| `DATABASE_URL` | URL de conexión a BD | `sqlite:///db.sqlite3` |

## Estructura del proyecto

```
ConectArte/
├── chat/               # App principal: modelos, vistas, API del marketplace
├── moderation/         # Panel de administración personalizado
├── conectarte_project/ # Configuración de Django (settings, urls, wsgi)
├── static/             # Archivos estáticos (CSS, JS, imágenes)
├── templates/          # Templates HTML
├── media/              # Imágenes subidas por usuarios (efímero en producción)
├── render.yaml         # Configuración de deploy en Render
├── start.sh            # Script de inicio para producción
└── requirements.txt    # Dependencias de Python
```

## Deploy en Render

1. Crea una cuenta en [render.com](https://render.com)
2. Conecta tu repositorio de GitHub
3. Render detecta automáticamente el `render.yaml` y configura:
   - Servicio web con Gunicorn
   - Base de datos PostgreSQL gratuita
   - Variables de entorno (SECRET_KEY, DATABASE_URL, etc.)
4. El deploy es automático

## Licencia

MIT
