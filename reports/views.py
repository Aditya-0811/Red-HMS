from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import csv
import json

from guests.models import Reservation, Bookmark
from rooms.models import Hotel, Room
from accounts.models import User, Notification
from billing.models import Invoice
from accounts.decorators import role_required, staff_required


@login_required
def dashboard(request):
    """
    Reference: user_dashboard/dashboard
    Staff see system-wide stats; guests see their own booking summary.
    """
    today            = timezone.now().date()
    this_month_start = today.replace(day=1)

    if request.user.is_staff_member:
        bookings          = Reservation.objects.filter(payment_status="paid")
        total_spent       = Reservation.objects.filter(payment_status="paid").aggregate(amount=Sum('total'))
        total_reservations  = Reservation.objects.count()
        active_reservations = Reservation.objects.filter(is_active=True, payment_status='paid').count()
        revenue_all_time    = total_spent.get('amount') or 0
        revenue_this_month  = (Reservation.objects.filter(payment_status='paid',
                                                           date__date__gte=this_month_start)
                               .aggregate(t=Sum('total'))['t'] or 0)
        total_rooms      = Room.objects.count()
        available_rooms  = Room.objects.filter(is_available=True).count()
        occupied_rooms   = total_rooms - available_rooms
        occupancy_rate   = round((occupied_rooms / total_rooms * 100), 1) if total_rooms else 0
        total_guests     = User.objects.filter(role='Guest').count()
        recent_reservations = Reservation.objects.select_related(
            'hotel', 'room_type', 'user', 'user__profile').prefetch_related('room').order_by('-date')[:10]
        todays_checkins  = Reservation.objects.filter(check_in_date=today,  payment_status='paid').count()
        todays_checkouts = Reservation.objects.filter(check_out_date=today, payment_status='paid').count()

        context = {
            'bookings':             bookings,
            'total_spent':          total_spent,
            'total_reservations':   total_reservations,
            'active_reservations':  active_reservations,
            'revenue_all_time':     revenue_all_time,
            'revenue_this_month':   revenue_this_month,
            'total_rooms':          total_rooms,
            'available_rooms':      available_rooms,
            'occupied_rooms':       occupied_rooms,
            'occupancy_rate':       occupancy_rate,
            'total_guests':         total_guests,
            'recent_reservations':  recent_reservations,
            'todays_checkins':      todays_checkins,
            'todays_checkouts':     todays_checkouts,
            'is_staff_view':        True,
        }
        from django.db.models.functions import TruncMonth
        revenue_by_month = list(
            Reservation.objects.filter(payment_status='paid')
            .annotate(month=TruncMonth('date')).values('month')
            .annotate(total=Sum('total')).order_by('month')
            .values_list('month', 'total')
        )[-6:]
        context['revenue_by_month'] = revenue_by_month
        arriving_today = Reservation.objects.filter(
            check_in_date=today, payment_status='paid'
        ).select_related('hotel', 'room_type', 'user').order_by('full_name')
        context['arriving_today'] = arriving_today
        all_rooms = Room.objects.select_related('hotel', 'room_type').order_by('hotel__name', 'room_number')
        context['all_rooms'] = all_rooms
    else:
        bookings    = Reservation.objects.filter(user=request.user, payment_status="paid")
        total_spent = Reservation.objects.filter(user=request.user, payment_status="paid").aggregate(amount=Sum('total'))
        context = {
            'bookings':         bookings,
            'total_spent':      total_spent,
            'my_reservations':  Reservation.objects.filter(user=request.user),
            'total_bookings':   Reservation.objects.filter(user=request.user).count(),
            'active_bookings':  Reservation.objects.filter(user=request.user, payment_status='paid', is_active=True).count(),
            'total_spent_amt':  total_spent.get('amount') or 0,
            'is_staff_view':    False,
        }
    return render(request, 'reports/dashboard.html', context)


@login_required
def booking_detail(request, booking_id):
    """Reference: dashboard/booking-detail/<booking_id>/"""
    from guests.models import Reservation
    reservation = Reservation.objects.get(booking_id=booking_id)
    return render(request, 'guests/reservation_detail.html', {'reservation': reservation})


@staff_required
def all_bookings(request):
    """Bookings list with status + search filters."""
    status_filter = request.GET.get('status', '')
    search_query  = request.GET.get('q', '').strip()

    if request.user.is_staff_member:
        reservations = Reservation.objects.select_related('hotel', 'room_type', 'user').order_by('-date')
    else:
        reservations = Reservation.objects.filter(user=request.user).order_by('-date')
        status_filter = ''

    if status_filter:
        reservations = reservations.filter(payment_status=status_filter)

    if search_query:
        reservations = reservations.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(hotel__name__icontains=search_query) |
            Q(booking_id__icontains=search_query)
        )

    filter_statuses = [
        ('',           'All',        '#1d1d1f'),
        ('paid',       'Paid',       '#27ae60'),
        ('processing', 'Processing', '#f39c12'),
        ('failed',     'Failed',     '#e74c3c'),
        ('cancelled',  'Cancelled',  '#7f8c8d'),
    ]

    return render(request, 'reports/all_bookings.html', {
        'reservations':   reservations,
        'status_filter':  status_filter,
        'search_query':   search_query,
        'filter_statuses': filter_statuses,
    })


@role_required('Admin', 'Manager')
def revenue_report(request):
    from django.db.models.functions import TruncMonth
    revenue_by_month = (
        Reservation.objects.filter(payment_status='paid')
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('-month')[:12]
    )
    monthly_target = request.session.get('monthly_target', 15000)
    if request.method == 'POST':
        try:
            t = int(request.POST.get('target', '15000'))
            request.session['monthly_target'] = t
            monthly_target = t
        except ValueError:
            pass
    revenue_with_variance = [
        {
            'month':    item['month'],
            'total':    item['total'],
            'variance': float(item['total']) - monthly_target,
            'pct':      min(round(float(item['total']) / monthly_target * 100 if monthly_target else 0), 130),
        }
        for item in revenue_by_month
    ]
    return render(request, 'reports/revenue_report.html', {
        'revenue_by_month':      revenue_by_month,
        'monthly_target':        monthly_target,
        'revenue_with_variance': revenue_with_variance,
    })


@role_required('Admin', 'Manager', 'Housekeeping')
def occupancy_report(request):
    hotels = Hotel.objects.filter(status='Live').annotate(
        total_rooms=Count('rooms'),
        available=Count('rooms', filter=Q(rooms__is_available=True)),
    )
    return render(request, 'reports/occupancy_report.html', {'hotels': hotels})


@login_required
def wallet(request):
    """Reference: dashboard/wallet/"""
    bookings    = Reservation.objects.filter(user=request.user, payment_status="paid")
    total_spent = Reservation.objects.filter(user=request.user, payment_status="paid").aggregate(amount=Sum('total'))
    from accounts.models import Profile
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'reports/wallet.html', {
        'bookings':             bookings,
        'total_spent':          total_spent,
        'wallet_balance':       profile.wallet,
        'wallet_transactions':  Reservation.objects.filter(
            user=request.user, payment_status='paid'
        ).order_by('-date').values('booking_id', 'total', 'date')[:10],
    })


@role_required('Admin', 'Manager')
def generate_report(request):
    """Generate a report by type and date range, save to Report model, display results."""
    from reports.models import Report
    from django.db.models.functions import TruncMonth

    REPORT_TYPES = [('Revenue', 'Revenue'), ('Occupancy', 'Occupancy'),
                    ('Guest', 'Guest'), ('Booking', 'Booking')]

    results = None
    report_type = ''
    data_from = data_to = None
    saved_report = None

    if request.method == 'POST':
        report_type = request.POST.get('report_type', '')
        data_from_str = request.POST.get('data_from', '')
        data_to_str   = request.POST.get('data_to', '')

        from datetime import date
        try:
            data_from = date.fromisoformat(data_from_str)
            data_to   = date.fromisoformat(data_to_str)
        except ValueError:
            messages.error(request, 'Invalid date range. Please try again.')
            return render(request, 'reports/generate_report.html', {'report_types': REPORT_TYPES})

        if data_from > data_to:
            messages.error(request, 'Start date must be before end date.')
            return render(request, 'reports/generate_report.html', {'report_types': REPORT_TYPES})

        if report_type == 'Revenue':
            results = (
                Reservation.objects.filter(
                    payment_status='paid',
                    date__date__gte=data_from,
                    date__date__lte=data_to,
                )
                .annotate(month=TruncMonth('date'))
                .values('month')
                .annotate(total=Sum('total'), count=Count('id'))
                .order_by('month')
            )
            total_revenue = Reservation.objects.filter(
                payment_status='paid',
                date__date__gte=data_from,
                date__date__lte=data_to,
            ).aggregate(t=Sum('total'))['t'] or 0

        elif report_type == 'Occupancy':
            from rooms.models import Hotel
            results = Hotel.objects.filter(status='Live').annotate(
                total_rooms=Count('rooms'),
                available=Count('rooms', filter=Q(rooms__is_available=True)),
            )
            total_revenue = None

        elif report_type == 'Guest':
            from accounts.models import User as U
            results = U.objects.filter(role='Guest', date_joined__date__gte=data_from,
                                       date_joined__date__lte=data_to)
            total_revenue = None

        elif report_type == 'Booking':
            results = Reservation.objects.filter(
                date__date__gte=data_from,
                date__date__lte=data_to,
            ).select_related('hotel', 'room_type', 'user').order_by('-date')
            total_revenue = None

        else:
            messages.error(request, 'Please select a valid report type.')
            return render(request, 'reports/generate_report.html', {'report_types': REPORT_TYPES})

        # Save a Report record so the Django admin list shows results
        title = f"{report_type} Report ({data_from} to {data_to})"
        saved_report = Report.objects.create(
            title=title,
            report_type=report_type,
            generated_by=request.user,
            data_from=data_from,
            data_to=data_to,
        )
        messages.success(request, f'Report "{title}" generated successfully.')

    recent_reports = Report.objects.all()[:10]
    return render(request, 'reports/generate_report.html', {
        'report_types':  REPORT_TYPES,
        'results':       results,
        'report_type':   report_type,
        'data_from':     data_from,
        'data_to':       data_to,
        'saved_report':  saved_report,
        'recent_reports': recent_reports,
        'total_revenue': locals().get('total_revenue'),
    })


from decimal import Decimal as _Decimal

@login_required
@require_POST
def wallet_topup(request):
    from django.http import JsonResponse
    from accounts.models import Profile
    try:
        amount = _Decimal(request.POST.get('amount', '0'))
        if amount <= 0 or amount > 10000:
            raise ValueError
    except Exception:
        return JsonResponse({'error': 'Invalid amount (1–10000)'}, status=400)
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.wallet += amount
    profile.save(update_fields=['wallet'])
    return JsonResponse({'balance': str(profile.wallet), 'added': str(amount)})


@login_required
def notifications(request):
    """Reference: dashboard/notifications/"""
    notifs = Notification.objects.filter(user=request.user, is_read=False)
    return render(request, 'accounts/notifications.html', {'notifications': notifs})


@login_required
def export_bookings_csv(request):
    reservations = (
        Reservation.objects.select_related('hotel', 'room_type', 'user').order_by('-date')
        if request.user.is_staff_member
        else Reservation.objects.filter(user=request.user).order_by('-date')
    )
    sf = request.GET.get('status', '')
    sq = request.GET.get('q', '').strip()
    if sf:
        reservations = reservations.filter(payment_status=sf)
    if sq:
        reservations = reservations.filter(
            Q(full_name__icontains=sq) | Q(email__icontains=sq) |
            Q(hotel__name__icontains=sq) | Q(booking_id__icontains=sq)
        )
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
    writer = csv.writer(response)
    writer.writerow(['Booking ID', 'Guest', 'Email', 'Hotel', 'Room Type',
                     'Check-In', 'Check-Out', 'Nights', 'Total', 'Status'])
    for r in reservations:
        writer.writerow([
            r.booking_id, r.full_name, r.email,
            r.hotel.name if r.hotel else '',
            r.room_type.type if r.room_type else '',
            r.check_in_date, r.check_out_date, r.nights, r.total, r.payment_status,
        ])
    return response


@login_required
@require_POST
def toggle_checkin(request, booking_id):
    res = get_object_or_404(Reservation, booking_id=booking_id)
    res.checked_in = not res.checked_in
    res.save(update_fields=['checked_in'])
    from guests.models import ActivityLog
    ActivityLog.objects.create(
        reservation=res, staff=request.user,
        description=f"Guest {'checked in' if res.checked_in else 'check-in reversed'} by {request.user.username}",
    )
    return JsonResponse({'checked_in': res.checked_in})


@login_required
@require_POST
def update_room_housekeeping(request):
    room = get_object_or_404(Room, id=request.POST.get('room_id'))
    room.is_available = (request.POST.get('status') == 'available')
    room.save(update_fields=['is_available'])
    return JsonResponse({'room_id': room.id, 'is_available': room.is_available})


@login_required
def send_booking_email(request, booking_id):
    from django.core.mail import send_mail
    if not request.user.is_staff_member:
        return JsonResponse({'error': 'Permission denied.'}, status=403)
    try:
        reservation = Reservation.objects.select_related('hotel', 'room_type').get(booking_id=booking_id)
    except Reservation.DoesNotExist:
        return JsonResponse({'error': 'Booking not found.'}, status=404)
    tpl = request.GET.get('tpl', request.POST.get('tpl', 'confirmation'))
    subject = f"Booking {'Confirmed' if tpl == 'confirmation' else 'Reminder'} — {reservation.hotel.name}"
    body = (
        f"Dear {reservation.full_name},\n\n"
        + (f"Your booking #{reservation.booking_id} at {reservation.hotel.name} is confirmed.\n\n"
           if tpl == 'confirmation'
           else f"Reminder: your check-in at {reservation.hotel.name} is tomorrow.\n\n")
        + f"Check-in: {reservation.check_in_date}\nCheck-out: {reservation.check_out_date}\n"
        + f"Total: ${reservation.total}\n\nWarm regards,\n{reservation.hotel.name} Team"
    )
    if request.GET.get('type') == 'preview':
        return JsonResponse({'subject': subject, 'body': body, 'to': reservation.email})
    if request.method == 'POST':
        try:
            send_mail(subject, body, None, [reservation.email], fail_silently=False)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST to send.'}, status=405)


@login_required
def booking_notes(request, booking_id):
    if not request.user.is_staff_member:
        return JsonResponse({'error': 'Permission denied.'}, status=403)
    reservation = get_object_or_404(Reservation, booking_id=booking_id)
    invoice, _ = Invoice.objects.get_or_create(
        reservation=reservation,
        defaults={'subtotal': reservation.total, 'total': reservation.total, 'issued_by': request.user},
    )
    try:
        notes = json.loads(invoice.notes or '[]')
    except Exception:
        notes = []
    if request.method == 'POST':
        action = request.POST.get('action', 'add')
        if action == 'add':
            text = request.POST.get('text', '').strip()[:500]
            if text:
                from datetime import datetime
                notes.append({
                    'id': max((n['id'] for n in notes), default=0) + 1,
                    'text': text,
                    'author': request.user.username,
                    'role': request.user.role,
                    'time': datetime.now().strftime('%d %b %Y %H:%M'),
                    'pinned': False,
                })
                invoice.notes = json.dumps(notes)
                invoice.save(update_fields=['notes'])
                return JsonResponse({'success': True, 'note': notes[-1]})
        elif action == 'pin':
            note_id = int(request.POST.get('note_id', 0))
            for n in notes:
                if n['id'] == note_id:
                    n['pinned'] = not n['pinned']
                    break
            invoice.notes = json.dumps(notes)
            invoice.save(update_fields=['notes'])
            return JsonResponse({'success': True})
        elif action == 'delete':
            notes = [n for n in notes if n['id'] != int(request.POST.get('note_id', 0))]
            invoice.notes = json.dumps(notes)
            invoice.save(update_fields=['notes'])
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Unknown action.'}, status=400)
    notes.sort(key=lambda x: (not x.get('pinned', False), x['id']))
    return JsonResponse({'notes': notes})
