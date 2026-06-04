from django.http import HttpResponseRedirect


class AdminAuthMiddleware:
    """
    Forces re-authentication via the custom login page before any /admin/ path
    is served, even when the user already holds an active main-site session.
    """
    EXEMPT_PREFIXES = (
        '/admin/login',
        '/admin/logout',
        '/admin/jsi18n',
        '/admin/autocomplete',
        '/admin/password_change',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            is_exempt = any(request.path.startswith(p) for p in self.EXEMPT_PREFIXES)
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if not is_exempt and not is_ajax:
                if not request.session.get('admin_authenticated'):
                    return HttpResponseRedirect(f'/admin/login/?next={request.path}')
        return self.get_response(request)
