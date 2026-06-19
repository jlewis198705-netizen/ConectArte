from django.db import models


class AdminUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'auth_user'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return self.username

    def get_username(self):
        return self.username


class AdminProfile(models.Model):
    ROLE_CHOICES = [
        ('client', 'Cliente'),
        ('artist', 'Artista'),
    ]
    user = models.OneToOneField(AdminUser, on_delete=models.CASCADE, related_name='profile', db_column='user_id')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='client')

    class Meta:
        managed = False
        db_table = 'chat_profile'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class AdminJobRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('assigned', 'Asignado'),
        ('completed', 'Completado'),
    ]

    client = models.ForeignKey(AdminUser, on_delete=models.RESTRICT, related_name='client_requests', db_column='client_id')
    artist = models.ForeignKey(AdminUser, on_delete=models.RESTRICT, related_name='artist_jobs', null=True, blank=True, db_column='artist_id')
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'chat_jobrequest'

    def __str__(self):
        return f"Solicitud #{self.id} - {self.client.username} ({self.status})"


class AdminMessage(models.Model):
    IMAGE_TYPE_CHOICES = [
        ('before', 'Antes'),
        ('after', 'Después'),
        ('progress', 'Progreso'),
    ]

    job_request = models.ForeignKey(AdminJobRequest, on_delete=models.RESTRICT, related_name='messages', db_column='job_request_id')
    sender = models.ForeignKey(AdminUser, on_delete=models.RESTRICT, related_name='sent_messages', db_column='sender_id')
    content = models.TextField()
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE_CHOICES, null=True, blank=True)
    image = models.ImageField(upload_to='job_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'chat_message'

    def __str__(self):
        return f"De {self.sender.username} en #{self.job_request.id}: {self.content[:30]}"


class AdminContentFlag(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('inappropriate', 'Inapropiado'),
    ]

    message_id = models.BigIntegerField(unique=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'admin_content_flags'

    def __str__(self):
        return f"Flag #{self.message_id}: {self.status}"
