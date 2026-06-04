from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/',               views.register_view,           name='register'),
    path('login/',                  views.login_view,              name='login'),
    path('logout/',                 views.logout_view,             name='logout'),
    path('profile/',                views.profile_view,            name='profile'),
    path('change-password/',        views.change_password_view,    name='change_password'),
    path('notifications/',          views.notifications_view,      name='notifications'),
    path('notifications/mark-seen/',views.mark_notification_seen,  name='mark_notification_seen'),
    path('notifications/filter/',   views.notification_filter,     name='notification_filter'),
    path('cart-count/',             views.cart_count,              name='cart_count'),
    path('notification-count/',     views.notification_count,      name='notification_count'),

    # ── Password Reset ────────────────────────────────────
    path('forgot-password/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url=reverse_lazy('accounts:password_reset_done'),
         ),
         name='password_reset'),
    path('forgot-password/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete'),
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]
