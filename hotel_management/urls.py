from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect

from guests.views import (
    add_to_selection, delete_selection, delete_session, add_to_bookmark,
)
from accounts.views import mark_notification_seen, notification_filter, cart_count
from billing.views import update_room_status, payment_success, payment_failed


def admin_login_redirect(request):
    """
    Send /admin/login/ to the custom login page, preserving ?next=.
    Also clears the admin_authenticated session flag so every visit to
    this URL requires explicit re-authentication.
    """
    request.session.pop('admin_authenticated', None)
    next_url = request.GET.get('next', '/admin/')
    return HttpResponseRedirect(f'/accounts/login/?next={next_url}')


urlpatterns = [
    # Intercept admin login → use our custom login page instead
    path('admin/login/', admin_login_redirect),
    path('admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    # ── App routes ───────────────────────────────────────
    path('',          include('rooms.urls',    namespace='rooms')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('guests/',   include('guests.urls',   namespace='guests')),
    path('billing/',  include('billing.urls',  namespace='billing')),
    path('reports/',  include('reports.urls',  namespace='reports')),

    # ── Reference-compatible AJAX shortcut paths ─────────
    path('booking/add_to_selection/',  add_to_selection),
    path('booking/delete_selection/',  delete_selection),
    path('booking/delete_session/',    delete_session),

    path('dashboard/add_to_bookmark/',           add_to_bookmark),
    path('dashboard/notification_mark_as_seen/', mark_notification_seen),
    path('dashboard/notification_filter/',       notification_filter),

    path('update_room_status/',           update_room_status),
    path('billing/update-room-status/',   update_room_status),

    path('accounts/cart-count/', cart_count),

    # ── Legacy reference-style payment URLs ──────────────
    path('success/<str:booking_id>/', payment_success),
    path('failed/<str:booking_id>/',  payment_failed),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
