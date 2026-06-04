from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from decimal import Decimal
from datetime import datetime

from rooms.models import Hotel, RoomType, Room
from .models import Reservation, Bookmark, Coupon
from accounts.models import Notification, Profile

DATE_FMT = "%Y-%m-%d"


# ── AJAX: Add room to session cart (GET, exactly like reference) ──────────────
def add_to_selection(request):
    """
    Adds a room to the session cart.
    POST (form submit) → reads request.POST, redirects to HTTP_REFERER.
    GET  (AJAX)        → reads request.GET,  returns JSON.
    """
    src = request.POST if request.method == 'POST' else request.GET
    rid = src.get('id')

    if not rid:
        if request.method == 'POST':
            messages.error(request, "Invalid room selection.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        return JsonResponse({'error': 'Missing id'}, status=400)

    checkin_val  = src.get('checkin', '').strip()
    checkout_val = src.get('checkout', '').strip()
    if request.method == 'POST' and (not checkin_val or not checkout_val):
        messages.error(request, "Please select check-in and check-out dates before adding a room.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    room_selection = {str(rid): {
        'hotel_id':       src.get('hotel_id', ''),
        'hotel_name':     src.get('hotel_name', ''),
        'room_name':      src.get('room_name', ''),
        'room_price':     src.get('room_price', '0'),
        'number_of_beds': src.get('number_of_beds', '1'),
        'room_number':    src.get('room_number', ''),
        'room_type':      src.get('room_type', ''),
        'room_id':        src.get('room_id', ''),
        'checkin':        src.get('checkin', ''),
        'checkout':       src.get('checkout', ''),
        'adult':          src.get('adult', '1'),
        'children':       src.get('children', '0'),
    }}

    if 'selection_data_obj' in request.session:
        if str(rid) in request.session['selection_data_obj']:
            sel = request.session['selection_data_obj']
            sel[str(rid)]['adult']    = room_selection[str(rid)]['adult']
            sel[str(rid)]['children'] = room_selection[str(rid)]['children']
            request.session['selection_data_obj'] = sel
        else:
            sel = request.session['selection_data_obj']
            sel.update(room_selection)
            request.session['selection_data_obj'] = sel
    else:
        request.session['selection_data_obj'] = room_selection

    if request.method == 'POST':
        room_number = src.get('room_number', '')
        label = f'Room {room_number}' if room_number else 'Room'
        messages.success(request, f'{label} added to your selection!')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # GET → JSON for AJAX callers
    return JsonResponse({
        'data': request.session['selection_data_obj'],
        'total_selected_items': len(request.session['selection_data_obj']),
    })


# ── AJAX: Delete one room from session cart ───────────────────────────────────
def delete_selection(request):
    """Reference: booking/delete_selection/"""
    rid = str(request.GET.get('id', ''))

    if 'selection_data_obj' in request.session:
        if rid in request.session['selection_data_obj']:
            sel = request.session['selection_data_obj']
            del sel[rid]
            request.session['selection_data_obj'] = sel

    # Recalculate totals for async response
    total = 0
    total_days = 0
    room_count = 0
    adult = 0
    children = 0
    checkin = ""
    checkout = ""
    hotel = None

    if 'selection_data_obj' in request.session and request.session['selection_data_obj']:
        for h_id, item in request.session['selection_data_obj'].items():
            try:
                checkin  = item.get("checkin", "")
                checkout = item.get("checkout", "")
                adult   += int(item.get("adult", 1))
                children += int(item.get("children", 0))
                rt_id    = item.get("room_type", "")
                hotel    = Hotel.objects.get(id=int(item.get("hotel_id", 0)))
                room_type = RoomType.objects.get(id=int(rt_id))

                if checkin and checkout:
                    ci = datetime.strptime(checkin, DATE_FMT)
                    co = datetime.strptime(checkout, DATE_FMT)
                    total_days = max((co - ci).days, 1)

                room_count += 1
                total += room_type.price * total_days
            except Exception:
                pass

    # Render the async partial template
    context_html = render_to_string('guests/async/selected_rooms.html', {
        'data':                 request.session.get('selection_data_obj', {}),
        'total_selected_items': len(request.session.get('selection_data_obj', {})),
        'total':       total,
        'total_days':  total_days,
        'adult':       adult,
        'children':    children,
        'checkin':     checkin,
        'checkout':    checkout,
        'hotel':       hotel,
    })

    return JsonResponse({
        'data': context_html,
        'total_selected_items': len(request.session.get('selection_data_obj', {})),
    })


# ── Clear entire session cart ─────────────────────────────────────────────────
def delete_session(request):
    request.session.pop('selection_data_obj', None)
    return redirect(request.META.get("HTTP_REFERER", "/"))


# ── Selected Rooms page (GET = display, POST = create booking) ─────────────────
def selected_rooms(request):
    if 'selection_data_obj' not in request.session or not request.session['selection_data_obj']:
        return render(request, 'guests/selected_rooms.html', {
            'data': {}, 'total_selected_items': 0,
            'total': 0, 'total_days': 0,
            'adult': 1, 'children': 0,
            'checkin': '', 'checkout': '', 'hotel': None,
        })

    if request.method == "POST":
        # Build reservation from session data (same logic as reference selected_rooms POST)
        total = 0
        room_count = 0
        total_days = 0
        hotel = None
        room_type = None
        checkin = ""
        checkout = ""
        adult = 1
        children = 0

        for h_id, item in request.session['selection_data_obj'].items():
            try:
                hotel     = Hotel.objects.get(id=int(item['hotel_id']))
                room      = Room.objects.get(id=int(item['room_id']))
                room_type = RoomType.objects.get(id=int(item['room_type']))
                checkin   = item.get('checkin', '')
                checkout  = item.get('checkout', '')
                adult     = int(item.get('adult', 1))
                children  = int(item.get('children', 0))
            except Exception:
                continue

        if not hotel or not room_type:
            messages.error(request, "Could not process your selection. Please try again.")
            return redirect('guests:selected_rooms')

        if not checkin or not checkout:
            messages.error(request, "Please select check-in and check-out dates before proceeding.")
            return redirect('guests:selected_rooms')

        try:
            ci = datetime.strptime(checkin, DATE_FMT)
            co = datetime.strptime(checkout, DATE_FMT)
        except ValueError:
            messages.error(request, "Invalid dates. Please re-select your check-in and check-out dates.")
            return redirect('guests:selected_rooms')
        total_days = max((co - ci).days, 1)

        full_name = request.POST.get("full_name", "")
        email     = request.POST.get("email", "")
        phone     = request.POST.get("phone", "")

        reservation = Reservation.objects.create(
            hotel=hotel,
            room_type=room_type,
            check_in_date=checkin,
            check_out_date=checkout,
            total_days=total_days,
            num_adults=adult,
            num_children=children,
            full_name=full_name,
            email=email,
            phone=phone,
            payment_status='processing',
        )

        if request.user.is_authenticated:
            reservation.user = request.user
            reservation.save()

        for h_id, item in request.session['selection_data_obj'].items():
            try:
                room = Room.objects.get(id=int(item["room_id"]))
                room_type_item = RoomType.objects.get(id=int(item["room_type"]))
                reservation.room.add(room)
                room_count += 1
                total += room_type_item.price * total_days
            except Exception:
                pass

        # Assign directly — reservation.total is float(0.0) after create()
        # (Django DecimalField default=0.00 stays as float until a DB read)
        safe_total = total if isinstance(total, Decimal) else Decimal(str(total))
        reservation.total           = safe_total
        reservation.before_discount = safe_total
        reservation.save()

        # ── Update user profile with billing info ──────────────
        if request.user.is_authenticated:
            try:
                profile, _ = Profile.objects.get_or_create(user=request.user)
                updated = False
                if full_name:
                    profile.full_name = full_name
                    updated = True
                if phone:
                    profile.phone = phone
                    updated = True
                if updated:
                    profile.save(update_fields=['full_name', 'phone'])
            except Exception:
                pass

            # ── Booking-pending notification ───────────────────
            Notification.objects.create(
                user=request.user,
                type='General',
                message=(
                    f"Booking #{reservation.booking_id} created at {hotel.name}. "
                    f"Check-in: {checkin} → Check-out: {checkout} "
                    f"({total_days} night(s)). "
                    f"Total: ${reservation.total:.2f}. "
                    f"Please complete your payment to confirm."
                ),
            )

        messages.success(request, "Almost there! Complete your payment to confirm the booking.")
        return HttpResponseRedirect(reverse('billing:payment', kwargs={'booking_id': reservation.booking_id}))

    # GET: build display context
    total      = 0
    room_count = 0
    total_days = 0
    adult      = 0
    children   = 0
    checkin    = ""
    checkout   = ""
    hotel      = None

    for h_id, item in request.session['selection_data_obj'].items():
        try:
            hotel     = Hotel.objects.get(id=int(item['hotel_id']))
            room_type = RoomType.objects.get(id=int(item['room_type']))
            checkin   = item.get('checkin', '')
            checkout  = item.get('checkout', '')
            adult    += int(item.get('adult', 1))
            children += int(item.get('children', 0))

            if checkin and checkout:
                ci = datetime.strptime(checkin, DATE_FMT)
                co = datetime.strptime(checkout, DATE_FMT)
                total_days = max((co - ci).days, 1)

            room_count += 1
            total += room_type.price * total_days
        except Exception:
            pass

    context = {
        'data':                 request.session['selection_data_obj'],
        'total_selected_items': len(request.session['selection_data_obj']),
        'total':       total,
        'total_days':  total_days,
        'adult':       adult,
        'children':    children,
        'checkin':     checkin,
        'checkout':    checkout,
        'hotel':       hotel,
    }
    return render(request, 'guests/selected_rooms.html', context)


# ── Bookmark toggle (AJAX) ────────────────────────────────────────────────────
def add_to_bookmark(request):
    """Reference: dashboard/add_to_bookmark/  (GET AJAX)"""
    hotel_id = request.GET.get('id')
    hotel    = get_object_or_404(Hotel, id=hotel_id)

    if not request.user.is_authenticated:
        return JsonResponse({"data": "Login To Bookmark Hotel", "icon": "warning"})

    bm = Bookmark.objects.filter(user=request.user, hotel=hotel)
    if bm.exists():
        bm.delete()
        return JsonResponse({"data": "Bookmark Deleted",   "icon": "success", "bookmarked": False})
    else:
        Bookmark.objects.create(user=request.user, hotel=hotel)
        return JsonResponse({"data": "Hotel Bookmarked",   "icon": "success", "bookmarked": True})


def toggle_bookmark(request, slug):
    """Standard page-redirect bookmark toggle."""
    hotel = get_object_or_404(Hotel, slug=slug)
    if not request.user.is_authenticated:
        messages.error(request, "Please login to bookmark hotels.")
        return redirect('accounts:login')

    bm = Bookmark.objects.filter(user=request.user, hotel=hotel)
    if bm.exists():
        bm.delete()
        messages.info(request, f"{hotel.name} removed from your wishlist.")
    else:
        Bookmark.objects.create(user=request.user, hotel=hotel)
        messages.success(request, f"{hotel.name} saved to wishlist!")
    return redirect('rooms:hotel_detail', slug=slug)


@login_required
def wishlist_view(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('hotel').prefetch_related('hotel__room_types')
    return render(request, 'guests/wishlist.html', {'bookmarks': bookmarks})


@login_required
def delete_bookmark(request, bid):
    Bookmark.objects.filter(id=bid, user=request.user).delete()
    messages.success(request, "Removed from wishlist.")
    return redirect('guests:wishlist')


# ── My Reservations ───────────────────────────────────────────────────────────
@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).select_related('hotel', 'room_type').prefetch_related('room')
    return render(request, 'guests/my_reservations.html', {'reservations': reservations})


@login_required
def reservation_detail(request, booking_id):
    reservation = get_object_or_404(Reservation, booking_id=booking_id, user=request.user)
    from .models import ActivityLog
    from billing.models import Payment
    activity_logs = ActivityLog.objects.filter(
        reservation=reservation).select_related('staff').order_by('date')
    payments = Payment.objects.filter(reservation=reservation)
    rooms = reservation.room.all()
    booking_fields = [
        ('Booking ID',      f'#{reservation.booking_id}'),
        ('Guest',           reservation.full_name),
        ('Email',           reservation.email),
        ('Phone',           reservation.phone or '—'),
        ('Payment Status',  reservation.get_payment_status_display()),
    ]
    return render(request, 'guests/reservation_detail.html', {
        'reservation':   reservation,
        'activity_logs': activity_logs,
        'payments':      payments,
        'rooms':         rooms,
        'booking_fields': booking_fields,
    })


SERVICE_CHOICES = ['Food', 'Cleaning', 'Laundry', 'Transport', 'Technical', 'Spa', 'Other']


@login_required
def request_room_service(request, booking_id):
    from billing.models import RoomService
    reservation = get_object_or_404(Reservation, booking_id=booking_id, user=request.user)
    if not reservation.checked_in:
        return JsonResponse({'error': 'You must be checked in to request room service.'}, status=400)
    if request.method == 'POST':
        svc_type = request.POST.get('service_type', 'Other')
        desc = request.POST.get('description', '').strip()[:500]
        room_id = request.POST.get('room_id', '')
        if svc_type not in SERVICE_CHOICES:
            return JsonResponse({'error': 'Invalid service type.'}, status=400)
        room_obj = None
        room_label = ''
        if room_id:
            try:
                room_obj = reservation.room.filter(id=int(room_id)).first()
                if room_obj:
                    room_label = f'Room {room_obj.room_number}'
            except (ValueError, TypeError):
                pass
        svc = RoomService.objects.create(
            reservation=reservation, room=room_obj,
            service_type=svc_type, description=desc, price=0.00,
        )
        if reservation.hotel and reservation.hotel.user:
            Notification.objects.create(
                user=reservation.hotel.user, type='General',
                message=f"Room service: {svc_type}{' for ' + room_label if room_label else ''} — #{booking_id} — {desc[:100]}",
            )
        from datetime import date
        return JsonResponse({
            'id': svc.id, 'service_type': svc.service_type,
            'room_label': room_label,
            'description': svc.description or '', 'date': str(date.today()), 'status': 'Pending',
        })
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def modification_request(request, booking_id):
    reservation = get_object_or_404(Reservation, booking_id=booking_id, user=request.user)
    if reservation.payment_status not in ('paid', 'processing'):
        return JsonResponse({'error': 'Only confirmed bookings can be modified.'}, status=400)
    if request.method == 'POST':
        req_type = request.POST.get('type', '')
        reason = request.POST.get('reason', '').strip()
        new_ci = request.POST.get('new_checkin', '')
        new_co = request.POST.get('new_checkout', '')
        if req_type not in ('modify', 'cancel'):
            return JsonResponse({'error': 'Invalid type.'}, status=400)
        msg = f"[{req_type.upper()}] #{booking_id} — {reservation.full_name}. "
        if req_type == 'modify' and new_ci and new_co:
            msg += f"Requested: {new_ci}→{new_co}. "
        msg += f"Reason: {reason}"
        from accounts.models import User as _User
        for admin in _User.objects.filter(role__in=['Admin', 'Manager']):
            Notification.objects.create(user=admin, type='General', message=msg)
        return JsonResponse({'success': True, 'message': 'Request submitted. Staff will contact you within 24 hours.'})
    return JsonResponse({'error': 'POST required.'}, status=405)
