import logging
from django.db import transaction
from django.db.models import Count, Q, Min
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import JobRequest, Message, Profile

logger = logging.getLogger(__name__)

def get_or_create_demo_artist():
    """
    Busca o crea un artista de demostración para asegurar que la asignación
    de la IA siempre tenga un destinatario válido.
    """
    artist_user, created = User.objects.get_or_create(
        username='artista_demo',
        defaults={'email': 'artista@conectarte.com', 'first_name': 'Artista', 'last_name': 'Demo'}
    )
    if created:
        artist_user.set_password('ConectArte2026!')
        artist_user.save()
    
    # Asegurar que el rol sea artista
    profile = artist_user.profile
    if profile.role != 'artist':
        profile.role = 'artist'
        profile.save()
        
    return artist_user


def get_or_create_system_user():
    """
    Obtiene o crea un usuario de sistema para firmar los mensajes automáticos de la IA.
    """
    system_user, created = User.objects.get_or_create(
        username='system_ia',
        defaults={'email': 'system@conectarte.com', 'is_active': False}
    )
    return system_user


def _select_artist_by_load_balancing(client_user):
    """
    Selecciona al artista con menos carga de trabajo activa.
    En caso de empate, usa round-robin (el que lleve más tiempo sin recibir asignación).
    """
    artists = User.objects.filter(profile__role='artist').exclude(id=client_user.id)

    if not artists.exists():
        return get_or_create_demo_artist()

    # Anotar cada artista con la cantidad de solicitudes activas (pending + assigned)
    artists_with_load = artists.annotate(
        active_count=Count('artist_jobs', filter=Q(
            Q(artist_jobs__status='pending') | Q(artist_jobs__status='assigned')
        ))
    )

    # Encontrar la carga mínima entre todos
    min_count = artists_with_load.aggregate(min_active=Min('active_count'))['min_active']

    # Filtrar solo los que tienen la carga mínima (empatados)
    # Ordenar por last_round_robin ascendente: NULLs primero (nunca asignados),
    # luego los que llevan más tiempo sin recibir asignación
    candidates = artists_with_load.filter(active_count=min_count).order_by('profile__last_round_robin')

    selected = candidates.first()

    # Actualizar el marcador round-robin
    profile = selected.profile
    profile.last_round_robin = timezone.now()
    profile.save(update_fields=['last_round_robin'])

    return selected


def classify_and_assign_job_request(job_request_id):
    """
    Implementa el requisito RF-02 y RF-04.
    Clasifica el servicio mediante balanceo de carga + round-robin y realiza
    la transición de estados 'pending' -> 'assigned' en una transacción atómica.
    Crea el mensaje de sistema inicial en la sala de chat.
    """
    try:
        with transaction.atomic():
            # select_for_update() bloquea la fila en MySQL para evitar condiciones de carrera (Race Conditions)
            job_request = JobRequest.objects.select_for_update().get(id=job_request_id)
            
            # Validar estado inicial
            if job_request.status != 'pending':
                raise ValidationError(
                    f"No se puede clasificar una solicitud en estado: {job_request.status}"
                )
            
            # Seleccionar artista por balanceo de carga + round-robin
            artist = _select_artist_by_load_balancing(job_request.client)
            
            # Transición del estado del ciclo de vida
            job_request.status = 'assigned'
            job_request.artist = artist
            job_request.save()
            
            # Crear el mensaje del sistema para activar el chat de negociación
            system_user = get_or_create_system_user()
            
            Message.objects.create(
                job_request=job_request,
                sender=system_user,
                content=(
                    f"[Sistema IA] Solicitud clasificada con éxito. Asignado al artista '{artist.first_name or artist.username}'. "
                    f"El canal de comunicación directa ahora está activo. ¡Pueden comenzar a negociar!"
                )
            )
            
            logger.info(f"Solicitud #{job_request.id} asignada atómicamente al artista {artist.username}")
            return job_request
            
    except JobRequest.DoesNotExist:
        logger.error(f"La solicitud con ID {job_request_id} no existe.")
        raise
    except Exception as e:
        logger.error(f"Error en la transacción atómica de asignación para #{job_request_id}: {str(e)}")
        raise
