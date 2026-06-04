from .models import Notification

def global_context(request):
    ctx = {}
    if request.user.is_authenticated:
        ctx['unread_notifications'] = Notification.objects.filter(
            user=request.user, is_read=False).count()
        try:
            ctx['user_profile'] = request.user.profile
        except Exception:
            ctx['user_profile'] = None
    # Cart count from session
    selection = request.session.get('selection_data_obj', {})
    ctx['selected_count'] = len(selection)
    return ctx
