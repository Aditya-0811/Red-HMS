from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import User, Profile, Notification
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, ChangePasswordForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('reports:dashboard')
    form = UserRegisterForm()
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                Profile.objects.get_or_create(
                    user=user,
                    defaults={'full_name': form.cleaned_data.get('full_name','')}
                )
            messages.success(request, "Account created! Please sign in.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Please fix the errors below.")
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    next_url = request.GET.get('next', '')
    # Skip auto-redirect for admin paths so users can re-authenticate
    if request.user.is_authenticated and not next_url.startswith('/admin/'):
        return redirect('reports:dashboard')
    if request.method == 'POST':
        from django.core.cache import cache
        x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_fwd.split(',')[0].strip() if x_fwd else request.META.get('REMOTE_ADDR', '')
        cache_key = f'login_attempts_{ip}'
        attempts = cache.get(cache_key, 0)
        if attempts >= 5:
            messages.error(request, 'Too many failed login attempts. Please try again in 15 minutes.')
            return render(request, 'accounts/login.html')
        email    = request.POST.get('email','').strip()
        password = request.POST.get('password','')
        user     = authenticate(request, username=email, password=password)
        # If email lookup failed, try matching by username
        if user is None:
            try:
                matched = User.objects.get(username__iexact=email)
                user = authenticate(request, username=matched.email, password=password)
            except User.DoesNotExist:
                pass
        if user:
            cache.delete(cache_key)
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', '')
            if next_url.startswith('/admin/'):
                # Grant explicit admin session access
                request.session['admin_authenticated'] = True
                return redirect(next_url)
            if next_url:
                return redirect(next_url)
            role_redirects = {
                'Admin':        'reports:dashboard',
                'Manager':      'reports:dashboard',
                'Receptionist': 'reports:all_bookings',
                'Housekeeping': 'reports:occupancy_report',
                'Guest':        'guests:my_reservations',
            }
            return redirect(role_redirects.get(user.role, 'reports:dashboard'))
        else:
            cache.set(cache_key, attempts + 1, timeout=900)
            messages.error(request, "Invalid email or password.")
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user_form    = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=profile)
    if request.method == 'POST':
        user_form    = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile')
        messages.error(request, "Please fix the errors below.")
    PROFILE_FIELDS = ['full_name', 'phone', 'gender', 'date_of_birth', 'country', 'city',
                      'address', 'identity_type', 'identity_image', 'image', 'facebook', 'twitter']
    filled = sum(1 for f in PROFILE_FIELDS if getattr(profile, f, None))
    profile_completion = round(filled / len(PROFILE_FIELDS) * 100)
    incomplete_fields = [f.replace('_', ' ').title() for f in PROFILE_FIELDS if not getattr(profile, f, None)]
    return render(request, 'accounts/profile.html', {
        'user_form': user_form, 'profile_form': profile_form, 'profile': profile,
        'profile_completion': profile_completion, 'incomplete_fields': incomplete_fields,
    })


@login_required
def change_password_view(request):
    form = ChangePasswordForm()
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if user.check_password(form.cleaned_data['old_password']):
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")
                return redirect('accounts:profile')
            messages.error(request, "Current password is incorrect.")
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'accounts/notifications.html', {'notifications': notifications})


def mark_notification_seen(request):
    """AJAX: mark a single notification as read."""
    from django.http import JsonResponse
    if request.user.is_authenticated:
        nid = request.GET.get('id')
        if nid:
            Notification.objects.filter(id=nid, user=request.user).update(is_read=True)
    return JsonResponse({'status': 'ok'})


def cart_count(request):
    """AJAX: return the number of rooms in the session cart."""
    from django.http import JsonResponse
    selection = request.session.get('selection_data_obj', {})
    return JsonResponse({'count': len(selection)})


@login_required
def notification_count(request):
    from django.http import JsonResponse
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


def notification_filter(request):
    """AJAX: filter notifications by read/unread – matches reference dashboard."""
    from django.template.loader import render_to_string
    from django.http import JsonResponse
    query = request.GET.get('query', 'all')
    if request.user.is_authenticated:
        if query == 'read':
            notifs = Notification.objects.filter(user=request.user, is_read=True)
        elif query == 'unread':
            notifs = Notification.objects.filter(user=request.user, is_read=False)
        else:
            notifs = Notification.objects.filter(user=request.user)
    else:
        notifs = Notification.objects.none()
    html = render_to_string('accounts/async/notifications.html', {'notifications': notifs})
    return JsonResponse({'data': html})
