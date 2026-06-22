import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils.html import escape

from django.db.models import Q
from django.db import connection
from .models import JobRequest, Message, Profile
from .services import classify_and_assign_job_request
from .forms import ChatMessageForm

# --- Vistas de Autenticación y Navegación ---

def index_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            username = data.get('username', '').strip()
            password = data.get('password', '')
            password2 = data.get('password2', '')
            role = data.get('role', 'client').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            
            if not username or not password:
                return JsonResponse({'error': 'El usuario y la contraseña son requeridos.'}, status=400)
                
            if len(password) < 8:
                return JsonResponse({'error': 'La contraseña debe tener al menos 8 caracteres.'}, status=400)
                
            if password != password2:
                return JsonResponse({'error': 'Las contraseñas no coinciden.'}, status=400)
                
            if role not in ['client', 'artist']:
                return JsonResponse({'error': 'Rol inválido.'}, status=400)
                
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'El nombre de usuario ya está registrado.'}, status=400)
            
            # Crear usuario
            user = User.objects.create_user(
                username=username, 
                password=password, 
                first_name=first_name, 
                last_name=last_name
            )
            
            # Asignar rol en el perfil
            profile = user.profile
            profile.role = role
            profile.save()
            
            # Iniciar sesión automáticamente
            login(request, user)
            return JsonResponse({'ok': True, 'redirect': '/dashboard/'})
            
        except Exception as e:
            return JsonResponse({'error': 'Error interno al registrar el usuario.'}, status=500)
            
    return render(request, 'chat/register.html')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'ok': True, 'redirect': '/dashboard/'})
        else:
            return JsonResponse({'error': 'Credenciales incorrectas.'}, status=400)
            
    return render(request, 'chat/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Renderiza la vista principal del software ConectArte.
    """
    user_role = request.user.profile.role
    return render(request, 'chat/dashboard.html', {
        'username': request.user.username,
        'role': user_role,
        'first_name': request.user.first_name,
    })


# --- Endpoints API del Dashboard (Stats) ---

@login_required
@require_http_methods(['GET'])
def dashboard_stats(request):
    user = request.user
    role = user.profile.role

    if role == 'client':
        qs = JobRequest.objects.filter(client=user)
    else:
        qs = JobRequest.objects.filter(Q(artist=user) | Q(status='pending'))

    return JsonResponse({
        'total': qs.count(),
        'pending': qs.filter(status='pending').count(),
        'assigned': qs.filter(status='assigned').count(),
        'completed': qs.filter(status='completed').count(),
    })


# --- Endpoints API del Ciclo de Vida del Servicio ---

@login_required
@require_http_methods(['GET'])
def list_job_requests(request):
    """
    Lista las solicitudes del usuario actual según su rol.
    """
    user = request.user
    role = user.profile.role
    
    if role == 'client':
        requests = JobRequest.objects.filter(client=user).order_by('-created_at')
    else:
        # Los artistas pueden ver los trabajos asignados a ellos y las solicitudes pendientes libres
        requests = JobRequest.objects.filter(Q(artist=user) | Q(status='pending')).order_by('-created_at')
        
    data = []
    for r in requests:
        data.append({
            'id': r.id,
            'client': r.client.username,
            'client_name': r.client.first_name or r.client.username,
            'artist': r.artist.username if r.artist else None,
            'artist_name': r.artist.first_name if r.artist else 'Sin asignar',
            'description': r.description,
            'status': r.status,
            'created_at': r.created_at.isoformat(),
        })
    return JsonResponse({'requests': data})


@login_required
@require_http_methods(['POST'])
def create_job_request(request):
    """
    Crea una solicitud artística en estado 'pending'. Solo permitido para clientes.
    """
    if request.user.profile.role != 'client':
        return JsonResponse({'error': 'Solo los clientes pueden crear solicitudes de servicio.'}, status=403)
        
    try:
        data = json.loads(request.body)
        description = data.get('description', '').strip()
        
        if not description:
            return JsonResponse({'error': 'La descripción del servicio no puede estar vacía.'}, status=400)
            
        job_request = JobRequest.objects.create(
            client=request.user,
            description=description,
            status='pending'
        )
        
        return JsonResponse({
            'ok': True,
            'job_request': {
                'id': job_request.id,
                'description': job_request.description,
                'status': job_request.status,
            }
        })
    except Exception as e:
        return JsonResponse({'error': 'Error al crear la solicitud.'}, status=500)


@login_required
@require_http_methods(['POST'])
def trigger_ai_classification(request, pk):
    """
    Simula la clasificación por parte de la IA (RF-02) que ejecuta 
    la asignación automática en una transacción atómica.
    """
    try:
        job_request = JobRequest.objects.get(id=pk)
        
        # Validación de propiedad
        if job_request.client != request.user:
            return JsonResponse({'error': 'No tienes permisos para modificar esta solicitud.'}, status=403)
            
        # Ejecutar la transacción de clasificación automática
        updated_request = classify_and_assign_job_request(pk)
        
        return JsonResponse({
            'ok': True,
            'job_request': {
                'id': updated_request.id,
                'status': updated_request.status,
                'artist': updated_request.artist.username if updated_request.artist else None,
                'artist_name': updated_request.artist.first_name if updated_request.artist else 'Sin asignar',
            }
        })
    except JobRequest.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada.'}, status=404)
    except ValidationError as ve:
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Error durante la clasificación de la IA.'}, status=500)


@login_required
@require_http_methods(['POST'])
def complete_job_request(request, pk):
    """
    Permite al cliente marcar la solicitud como completada (RF-03).
    """
    try:
        job_request = JobRequest.objects.get(id=pk)
        
        if job_request.client != request.user:
            return JsonResponse({'error': 'Solo el cliente que creó la solicitud puede finalizarla.'}, status=403)
            
        if job_request.status != 'assigned':
            return JsonResponse({'error': 'Solo se pueden completar solicitudes en estado asignado.'}, status=400)
            
        job_request.status = 'completed'
        job_request.save()
        
        # Enviar mensaje de sistema indicando que el servicio finalizó
        system_user, _ = User.objects.get_or_create(username='system_ia', defaults={'is_active': False})
        Message.objects.create(
            job_request=job_request,
            sender=system_user,
            content="[Sistema IA] El servicio ha sido marcado como COMPLETADO. El chat ahora está en modo de solo lectura para fines de auditoría de calidad."
        )
        
        return JsonResponse({'ok': True, 'status': job_request.status})
        
    except JobRequest.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Error al actualizar la solicitud.'}, status=500)


# --- Endpoints API Antes/Después ---

def _get_inappropriate_image_ids():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT message_id FROM admin_content_flags WHERE status = 'inappropriate'")
            return {row[0] for row in cursor.fetchall()}
    except Exception:
        return set()

@login_required
@require_http_methods(['GET'])
def get_before_after(request, pk):
    """
    Recupera las imágenes 'before' y 'after' de una solicitud específica.
    Retorna URLs de ambas imágenes (o null si no existen).
    """
    try:
        job_request = JobRequest.objects.get(id=pk)
        user = request.user

        if user != job_request.client and user != job_request.artist and not user.is_staff:
            return HttpResponseForbidden("Acceso denegado.")

        inappropriate_ids = _get_inappropriate_image_ids()
        before_msg = Message.objects.filter(job_request=job_request, image_type='before').exclude(image='').exclude(id__in=inappropriate_ids).last()
        after_msg = Message.objects.filter(job_request=job_request, image_type='after').exclude(image='').exclude(id__in=inappropriate_ids).last()

        return JsonResponse({
            'before': {
                'image_url': before_msg.image.url if before_msg and before_msg.image else None,
                'message_id': before_msg.id if before_msg else None,
                'created_at': before_msg.created_at.isoformat() if before_msg else None,
            },
            'after': {
                'image_url': after_msg.image.url if after_msg and after_msg.image else None,
                'message_id': after_msg.id if after_msg else None,
                'created_at': after_msg.created_at.isoformat() if after_msg else None,
            },
        })
    except JobRequest.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Error al obtener imágenes.'}, status=500)


# --- Endpoints API del Módulo de Mensajería (Chat) ---

@login_required
@require_http_methods(['GET'])
def get_messages(request, pk):
    """
    Obtiene los mensajes de una solicitud de trabajo.
    Seguridad: Valida que el usuario sea el cliente o el artista asociado.
    Polling: Admite un parámetro 'since' para recibir solo los mensajes nuevos.
    """
    try:
        job_request = JobRequest.objects.get(id=pk)
        user = request.user
        
        # VALIDACIÓN DE PRIVACIDAD: El usuario DEBE ser parte de este contrato de chat
        if user != job_request.client and user != job_request.artist and not user.is_staff:
            return HttpResponseForbidden("Acceso denegado: No eres participante de este contrato de negociación.")
            
        messages = Message.objects.filter(job_request=job_request)

        inappropriate_ids = _get_inappropriate_image_ids()
        messages = messages.exclude(id__in=inappropriate_ids)
        
        since_id = request.GET.get('since')
        if since_id:
            try:
                messages = messages.filter(id__gt=int(since_id))
            except ValueError:
                return HttpResponseBadRequest("Parámetro 'since' inválido.")
        
        messages_data = []
        for m in messages:
            msg_data = {
                'id': m.id,
                'sender': m.sender.username,
                'sender_name': m.sender.first_name or m.sender.username,
                'content': m.content,
                'image_type': m.image_type,
                'image_url': m.image.url if m.image else None,
                'created_at': m.created_at.isoformat(),
                'is_deleted': m.is_deleted,
            }
            messages_data.append(msg_data)
            
        return JsonResponse({
            'messages': messages_data,
            'status': job_request.status
        })
        
    except JobRequest.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Error al recuperar mensajes.'}, status=500)


@login_required
@require_http_methods(['POST'])
def send_message(request, pk):
    """
    Envía un mensaje al chat asociado a la solicitud.
    Seguridad:
    1. Valida membresía de chat.
    2. Bloquea el envío si la solicitud está 'completed' (solo lectura).
    3. Sanitiza contenido.
    Soporta: texto, imágenes (before/after/progress) o ambos.
    """
    try:
        job_request = JobRequest.objects.get(id=pk)
        user = request.user
        
        # 1. VALIDACIÓN DE PRIVACIDAD: Sólo las partes involucradas pueden escribir
        if user != job_request.client and user != job_request.artist:
            return HttpResponseForbidden("Acceso denegado: No puedes enviar mensajes a este chat.")
            
        # 2. BLOQUEAR SI ESTÁ COMPLETADO (Modo solo lectura)
        if job_request.status == 'completed':
            return JsonResponse({'error': 'El chat está cerrado porque el servicio ha finalizado.'}, status=400)
        
        # 3. Procesar formulario multipart (soporta JSON y form-data con archivos)
        if request.content_type and 'multipart/form-data' in request.content_type:
            form = ChatMessageForm(request.POST, request.FILES)
            if not form.is_valid():
                errors = form.errors.as_json()
                return JsonResponse({'error': errors}, status=400)
            
            content = form.cleaned_data.get('content', '').strip()
            image = form.cleaned_data.get('image')
            image_type = form.cleaned_data.get('image_type')
            
            if not content and not image:
                return JsonResponse({'error': 'Debe proporcionar un mensaje o una imagen.'}, status=400)
                
            if content and len(content) > 1000:
                return JsonResponse({'error': 'El mensaje es demasiado largo (máximo 1000 caracteres).'}, status=400)
                
            sanitized_content = escape(content) if content else ''
            
            message = Message.objects.create(
                job_request=job_request,
                sender=user,
                content=sanitized_content,
                image=image,
                image_type=image_type,
            )
        else:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'error': 'El mensaje no puede estar vacío.'}, status=400)
                
            if len(content) > 1000:
                return JsonResponse({'error': 'El mensaje es demasiado largo (máximo 1000 caracteres).'}, status=400)
                
            sanitized_content = escape(content)
            
            message = Message.objects.create(
                job_request=job_request,
                sender=user,
                content=sanitized_content,
            )
        
        return JsonResponse({
            'ok': True,
            'message': {
                'id': message.id,
                'sender': message.sender.username,
                'sender_name': message.sender.first_name or message.sender.username,
                'content': message.content,
                'image_type': message.image_type,
                'image_url': message.image.url if message.image else None,
                'created_at': message.created_at.isoformat(),
            }
        })
        
    except JobRequest.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada.'}, status=404)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Error al enviar mensaje (posible imagen)")
        return JsonResponse({'error': str(e)}, status=500)
