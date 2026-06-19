from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.template import loader
from django.utils.cache import add_never_cache_headers


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_active and request.user.is_staff:
            response = view_func(request, *args, **kwargs)
            add_never_cache_headers(response)
            return response

        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            path = request.build_absolute_uri()
            return redirect_to_login(path, '/admin-panel/login/')

        t = loader.get_template('moderation/forbidden.html')
        response = HttpResponseForbidden(t.render(request=request))
        add_never_cache_headers(response)
        return response

    return _wrapped_view
