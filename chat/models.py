from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    Perfil de usuario para extender el modelo User con roles específicos.
    """
    ROLE_CHOICES = [
        ('client', 'Cliente'),
        ('artist', 'Artista'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='client')
    last_round_robin = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class JobRequest(models.Model):
    """
    Solicitud de servicio artístico. 
    Contiene restricciones CHECK para asegurar los estados válidos del ciclo de vida.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('assigned', 'Asignado'),
        ('completed', 'Completado'),
    ]
    
    # ON DELETE RESTRICT en las relaciones principales para proteger el historial de obras
    client = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='client_requests')
    artist = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='artist_jobs', null=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Restricción CHECK a nivel de base de datos
            models.CheckConstraint(
                condition=models.Q(status__in=['pending', 'assigned', 'completed']),
                name='check_job_request_status'
            )
        ]

    def __str__(self):
        return f"Solicitud #{self.id} - {self.client.username} ({self.status})"


class Message(models.Model):
    """
    Mensajes del chat de negociación y seguimiento asociados a una solicitud de trabajo.
    Usa ON DELETE RESTRICT para proteger el historial legal de conversaciones.
    """
    IMAGE_TYPE_CHOICES = [
        ('before', 'Antes'),
        ('after', 'Después'),
        ('progress', 'Progreso'),
    ]

    # Restricción referencial fuerte para proteger la conversación
    job_request = models.ForeignKey(JobRequest, on_delete=models.RESTRICT, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='sent_messages')
    content = models.TextField()
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, null=True, blank=True)
    image = models.ImageField(upload_to='job_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        # Índice compuesto para optimizar el polling recurrente: WHERE job_request_id = ? ORDER BY created_at
        indexes = [
            models.Index(fields=['job_request', 'created_at'], name='idx_msg_job_request_created'),
        ]

    def __str__(self):
        return f"De {self.sender.username} en #{self.job_request.id}: {self.content[:30]}"


# Señales para crear/guardar automáticamente el perfil del usuario al registrarse
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)
