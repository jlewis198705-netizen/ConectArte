from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from .models import JobRequest, Message, Profile
from .services import classify_and_assign_job_request, get_or_create_demo_artist

class ConectArteTestCase(TestCase):
    
    def setUp(self):
        # Crear usuarios de prueba
        self.client_user = User.objects.create_user(username='cliente1', password='Password123!')
        self.client_user.profile.role = 'client'
        self.client_user.profile.save()
        
        self.artist_user = User.objects.create_user(username='artista1', password='Password123!')
        self.artist_user.profile.role = 'artist'
        self.artist_user.profile.save()
        
        self.intruder_user = User.objects.create_user(username='intruso1', password='Password123!')
        self.intruder_user.profile.role = 'client'
        self.intruder_user.profile.save()
        
        # Cliente HTTP de Django para llamadas de API
        self.http_client = Client()

    def test_job_request_creation_and_default_status(self):
        """
        Verifica que una solicitud se cree correctamente con el estado 'pending' por defecto.
        """
        req = JobRequest.objects.create(
            client=self.client_user,
            description="Restauración de mural colonial."
        )
        self.assertEqual(req.status, 'pending')
        self.assertIsNone(req.artist)

    def test_check_constraint_status(self):
        """
        Verifica que la restricción CHECK impida guardar estados inválidos.
        """
        req = JobRequest(
            client=self.client_user,
            description="Proyecto de prueba",
            status="invalid_state"  # No está en 'pending', 'assigned', 'completed'
        )
        # En bases de datos que soportan CHECK (como MySQL), esto arroja un IntegrityError
        # o Django falla al validar el modelo si usamos full_clean()
        with self.assertRaises((IntegrityError, ValidationError)):
            req.full_clean()
            req.save()

    def test_atomic_transaction_ai_assignment(self):
        """
        Verifica la transacción atómica (RF-02): la clasificación por IA
        asigna un artista, cambia el estado a 'assigned' y crea el mensaje inicial.
        """
        req = JobRequest.objects.create(
            client=self.client_user,
            description="Mural decorativo en terraza."
        )
        
        # Ejecutar la asignación automática de la IA
        updated_req = classify_and_assign_job_request(req.id)
        
        # Verificar cambios
        self.assertEqual(updated_req.status, 'assigned')
        self.assertIsNotNone(updated_req.artist)
        
        # Verificar que el mensaje inicial de sistema se creó correctamente
        messages = Message.objects.filter(job_request=updated_req)
        self.assertEqual(messages.count(), 1)
        self.assertEqual(messages.first().sender.username, 'system_ia')

    def test_atomic_transaction_rollback_on_failure(self):
        """
        Verifica que si la transición falla (ej: la solicitud no está 'pending'),
        toda la transacción se revierte y no se crean mensajes del sistema.
        """
        req = JobRequest.objects.create(
            client=self.client_user,
            description="Restauración antigua.",
            status="completed" # Ya está completado
        )
        
        # Intentar clasificar debe fallar por validación de estado
        with self.assertRaises(ValidationError):
            classify_and_assign_job_request(req.id)
            
        # Verificar que NO se crearon mensajes para esta solicitud
        messages = Message.objects.filter(job_request=req)
        self.assertEqual(messages.count(), 0)

    def test_referential_integrity_on_delete_restrict(self):
        """
        Verifica la regla ON DELETE RESTRICT: no se puede eliminar un JobRequest
        si contiene mensajes de chat asociados.
        """
        req = JobRequest.objects.create(
            client=self.client_user,
            description="Retrato al óleo.",
            status="assigned",
            artist=self.artist_user
        )
        
        # Crear un mensaje
        Message.objects.create(
            job_request=req,
            sender=self.client_user,
            content="Hola artista, ¿cuándo empezamos?"
        )
        
        # Intentar eliminar la solicitud debe fallar debido a RESTRICT
        with self.assertRaises(IntegrityError):
            req.delete()

    def test_chat_privacy_access_control(self):
        """
        Verifica que solo los participantes autorizados puedan ver o enviar mensajes.
        """
        req = JobRequest.objects.create(
            client=self.client_user,
            description="Mural en oficina.",
            status="assigned",
            artist=self.artist_user
        )
        
        # 1. Intentar acceder como intruso (no participante)
        self.http_client.login(username='intruso1', password='Password123!')
        
        # Intentar obtener mensajes
        url_get = reverse('get_messages', kwargs={'pk': req.id})
        response = self.http_client.get(url_get)
        self.assertEqual(response.status_code, 403)
        
        # Intentar enviar un mensaje
        url_send = reverse('send_message', kwargs={'pk': req.id})
        response = self.http_client.post(url_send, data='{"content": "Hack!"}', content_type='application/json')
        self.assertEqual(response.status_code, 403)
        
        # 2. Acceder como participante (Cliente)
        self.http_client.login(username='cliente1', password='Password123!')
        response = self.http_client.get(url_get)
        self.assertEqual(response.status_code, 200)

    def test_chat_read_only_when_completed(self):
        """
        Verifica que una vez completado el servicio, no se puedan enviar más mensajes (chat cerrado).
        """
        req = JobRequest.objects.create(
            client=self.client_user,
            description="Mural de prueba.",
            status="completed",
            artist=self.artist_user
        )
        
        # Iniciar sesión como cliente
        self.http_client.login(username='cliente1', password='Password123!')
        
        # Intentar enviar mensaje en chat completado
        url_send = reverse('send_message', kwargs={'pk': req.id})
        response = self.http_client.post(
            url_send, 
            data='{"content": "Mensaje en chat completado"}', 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cerrado", response.json()['error'])
