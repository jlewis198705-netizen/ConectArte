import json
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.db.models import Count, Q
from .models import AdminUser, AdminProfile, AdminJobRequest, AdminMessage, AdminContentFlag
from .decorators import admin_required


@require_http_methods(['GET', 'POST'])
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('mod_login')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('mod_dashboard')

    error = None
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('mod_dashboard')
        error = 'Credenciales incorrectas o no tienes permisos de administrador.'

    redirected = request.GET.get('next') is not None and request.user.is_authenticated

    return render(request, 'moderation/login.html', {
        'error': error,
        'redirected': redirected,
    })


@admin_required
def dashboard_view(request):
    total_artists = AdminUser.objects.filter(
        profile__role='artist', is_active=True
    ).count()

    active_clients = AdminUser.objects.filter(
        profile__role='client', is_active=True
    ).count()

    ongoing_negotiations = AdminJobRequest.objects.exclude(
        status='completed'
    ).count()

    completed_jobs = AdminJobRequest.objects.filter(
        status='completed'
    ).count()

    pending_review = AdminMessage.objects.filter(
        image_type__isnull=False
    ).exclude(image='').count()

    return render(request, 'moderation/index.html', {
        'total_artists': total_artists,
        'active_clients': active_clients,
        'ongoing_negotiations': ongoing_negotiations,
        'completed_jobs': completed_jobs,
        'pending_review': pending_review,
        'admin_name': request.user.first_name or request.user.username,
    })


@admin_required
def artist_list_view(request):
    artists = AdminUser.objects.filter(
        profile__role='artist'
    ).select_related('profile').annotate(
        active_jobs=Count('artist_jobs', filter=Q(artist_jobs__status__in=['pending', 'assigned'])),
        completed_jobs=Count('artist_jobs', filter=Q(artist_jobs__status='completed')),
    ).order_by('username')

    return render(request, 'moderation/artists.html', {
        'artists': artists,
        'admin_name': request.user.first_name or request.user.username,
    })


@admin_required
@csrf_exempt
@require_http_methods(['POST'])
def toggle_artist_view(request, user_id):
    try:
        user = AdminUser.objects.get(pk=user_id)
        profile = AdminProfile.objects.get(user=user)
        if profile.role != 'artist':
            return JsonResponse({'error': 'El usuario no es un artista.'}, status=400)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({
            'ok': True,
            'is_active': user.is_active,
            'status': 'activado' if user.is_active else 'desactivado',
        })
    except AdminUser.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado.'}, status=404)


@admin_required
@csrf_exempt
@require_http_methods(['POST'])
def delete_artist_view(request, user_id):
    try:
        user = AdminUser.objects.get(pk=user_id)
        profile = AdminProfile.objects.get(user=user)
        if profile.role != 'artist':
            return JsonResponse({'error': 'El usuario no es un artista.'}, status=400)

        has_jobs = AdminJobRequest.objects.filter(artist=user).exists()
        if has_jobs:
            return JsonResponse({
                'error': 'No se puede eliminar: el artista tiene trabajos asociados. Desactívalo en su lugar.'
            }, status=409)

        user.delete()
        return JsonResponse({'ok': True})
    except AdminUser.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_required
@csrf_exempt
@require_http_methods(['POST'])
def delete_client_view(request, user_id):
    try:
        user = AdminUser.objects.get(pk=user_id)
        profile = AdminProfile.objects.get(user=user)
        if profile.role != 'client':
            return JsonResponse({'error': 'El usuario no es un cliente.'}, status=400)

        has_jobs = AdminJobRequest.objects.filter(client=user).exists()
        if has_jobs:
            return JsonResponse({
                'error': 'No se puede eliminar: el cliente tiene solicitudes asociadas. Desactívalo en su lugar.'
            }, status=409)

        user.delete()
        return JsonResponse({'ok': True})
    except AdminUser.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_required
def client_list_view(request):
    clients = AdminUser.objects.filter(
        profile__role='client'
    ).select_related('profile').annotate(
        total_requests=Count('client_requests'),
    ).order_by('username')

    return render(request, 'moderation/clients.html', {
        'clients': clients,
        'admin_name': request.user.first_name or request.user.username,
    })


@admin_required
@csrf_exempt
@require_http_methods(['POST'])
def toggle_client_view(request, user_id):
    try:
        user = AdminUser.objects.get(pk=user_id)
        profile = AdminProfile.objects.get(user=user)
        if profile.role != 'client':
            return JsonResponse({'error': 'El usuario no es un cliente.'}, status=400)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({
            'ok': True,
            'is_active': user.is_active,
            'status': 'activado' if user.is_active else 'desactivado',
        })
    except AdminUser.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado.'}, status=404)


@admin_required
def content_review_view(request):
    messages_with_images = AdminMessage.objects.filter(
        image_type__isnull=False
    ).exclude(image='').select_related(
        'job_request', 'sender'
    ).order_by('-created_at')

    flags = {
        f.message_id: f
        for f in AdminContentFlag.objects.all()
    }

    items = []
    for msg in messages_with_images:
        flag = flags.get(msg.id)
        items.append({
            'message': msg,
            'flag_status': flag.status if flag else 'pending',
            'flag_id': flag.id if flag else None,
        })

    return render(request, 'moderation/content.html', {
        'items': items,
        'admin_name': request.user.first_name or request.user.username,
    })


@csrf_exempt
def content_action_view(request, message_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': f'No autorizado ({request.user})'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

    try:
        message = AdminMessage.objects.get(pk=message_id)
        if not message.image_type or not message.image:
            return JsonResponse({'error': 'Este mensaje no contiene una imagen para revisar.'}, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Body inválido.'}, status=400)
        action = data.get('action')

        if action == 'delete':
            message.is_deleted = True
            message.content = ''
            if message.image:
                message.image.delete(save=False)
                message.image = None
                message.image_type = None
            message.save()
            return JsonResponse({'ok': True, 'label': 'Eliminado'})

        if action not in ('approved', 'inappropriate'):
            return JsonResponse({'error': 'Acción inválida. Use "approved" o "inappropriate".'}, status=400)

        flag, created = AdminContentFlag.objects.get_or_create(
            message_id=message.id,
            defaults={'status': action, 'reviewed_at': datetime.now()},
        )
        if not created:
            flag.status = action
            flag.reviewed_at = datetime.now()
            flag.save()

        return JsonResponse({
            'ok': True,
            'status': flag.status,
            'label': 'Aprobado' if flag.status == 'approved' else 'Inapropiado',
        })
    except AdminMessage.DoesNotExist:
        return JsonResponse({'error': 'Mensaje no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@admin_required
@csrf_exempt
@require_http_methods(['POST'])
def delete_job_request_view(request, job_id):
    try:
        job_request = AdminJobRequest.objects.get(pk=job_id)
        messages = AdminMessage.objects.filter(job_request=job_request)

        for msg in messages:
            if msg.image:
                msg.image.delete(save=False)
            msg.delete()

        job_request.delete()

        return JsonResponse({'ok': True})
    except AdminJobRequest.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_required
@csrf_exempt
@require_http_methods(['POST'])
def delete_message_image_view(request, message_id):
    try:
        msg = AdminMessage.objects.get(pk=message_id)
        if not msg.image:
            return JsonResponse({'error': 'El mensaje no tiene imagen.'}, status=400)

        msg.image.delete(save=False)
        msg.image = None
        msg.image_type = None
        msg.save()

        return JsonResponse({'ok': True})
    except AdminMessage.DoesNotExist:
        return JsonResponse({'error': 'Mensaje no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@admin_required
def negotiations_view(request):
    job_requests = AdminJobRequest.objects.select_related(
        'client', 'artist'
    ).order_by('-created_at')

    jobs_data = []
    for jr in job_requests:
        messages = AdminMessage.objects.filter(
            job_request=jr
        ).select_related('sender').order_by('created_at')

        jobs_data.append({
            'job': jr,
            'messages': messages,
            'message_count': messages.count(),
        })

    return render(request, 'moderation/negotiations.html', {
        'jobs_data': jobs_data,
        'admin_name': request.user.first_name or request.user.username,
    })
