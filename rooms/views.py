from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Hotel, RoomType, Room, Review
from datetime import date as _date


def get_season_context():
    m = _date.today().month
    if m in (6, 7, 8):
        return {'season': 'Peak Season', 'season_emoji': '🌞', 'season_multiplier': 1.30,
                'season_color': '#f59e0b', 'season_note': 'High demand — prices 30% above base.'}
    elif m in (9, 10, 11):
        return {'season': 'Shoulder Season', 'season_emoji': '🍂', 'season_multiplier': 1.00,
                'season_color': '#06b6d4', 'season_note': 'Standard rates apply.'}
    else:
        return {'season': 'Low Season', 'season_emoji': '❄️', 'season_multiplier': 0.85,
                'season_color': '#22c55e', 'season_note': 'Save up to 15% in low season!'}


def index(request):
    hotels   = Hotel.objects.filter(status="Live")
    featured = hotels.filter(featured=True)
    return render(request, 'hotel/index.html', {'hotels': hotels, 'featured': featured})


def hotel_listing(request):
    hotels    = Hotel.objects.filter(status="Live").prefetch_related(
        'room_types', 'gallery', 'reviews', 'features').select_related('user')
    query     = request.GET.get('q', '')
    city      = request.GET.get('city', '')
    room_type = request.GET.get('type', '')
    if query:     hotels = hotels.filter(name__icontains=query)
    if city:      hotels = hotels.filter(city__icontains=city)
    if room_type: hotels = hotels.filter(room_types__type=room_type).distinct()
    return render(request, 'hotel/hotel_listing.html', {
        'hotels': hotels, 'query': query,
        'city': city, 'room_type': room_type,
        'hotel_count': hotels.count(),
    })


def hotel_count_ajax(request):
    from django.http import JsonResponse
    hotels = Hotel.objects.filter(status='Live')
    q    = request.GET.get('q', '')
    city = request.GET.get('city', '')
    rt   = request.GET.get('type', '')
    if q:    hotels = hotels.filter(name__icontains=q)
    if city: hotels = hotels.filter(city__icontains=city)
    if rt:   hotels = hotels.filter(room_types__type=rt).distinct()
    return JsonResponse({'count': hotels.count()})


def hotel_detail(request, slug):
    hotel = get_object_or_404(Hotel, status="Live", slug=slug)
    hotel.views += 1
    hotel.save(update_fields=['views'])
    all_reviews = hotel.reviews.filter(active=True).select_related('user', 'user__profile')
    user_review = all_reviews.filter(user=request.user).first() if request.user.is_authenticated else None
    bookmark    = None
    if request.user.is_authenticated:
        from guests.models import Bookmark
        bookmark = Bookmark.objects.filter(user=request.user, hotel=hotel).first()
    total_reviews = all_reviews.count()
    rating_breakdown = [
        (stars, cnt, round(cnt / total_reviews * 100) if total_reviews else 0)
        for stars in range(5, 0, -1)
        for cnt in [all_reviews.filter(rating=stars).count()]
    ]
    from guests.models import Reservation as GuestReservation
    verified_reviewers = set(
        GuestReservation.objects.filter(hotel=hotel, payment_status='paid')
        .exclude(user=None).values_list('user_id', flat=True)
    )
    from datetime import date
    min_price = RoomType.objects.filter(hotel=hotel).order_by('price').values_list('price', flat=True).first()
    context = {
        'hotel': hotel, 'all_reviews': all_reviews,
        'user_review': user_review, 'bookmark': bookmark,
        'today': date.today().isoformat(),
        'faqs': hotel.faqs.filter(active=True),
        'rating_breakdown': rating_breakdown,
        'verified_reviewers': verified_reviewers,
        'min_price': min_price or 0,
        'checkin':  request.GET.get('checkin', ''),
        'checkout': request.GET.get('checkout', ''),
        'adults':   request.GET.get('adult', '1'),
        'children': request.GET.get('children', '0'),
    }
    context.update(get_season_context())
    return render(request, 'hotel/hotel_detail.html', context)


def room_type_detail(request, slug, rt_slug):
    hotel     = get_object_or_404(Hotel, status="Live", slug=slug)
    room_type = get_object_or_404(RoomType, hotel=hotel, slug=rt_slug)
    checkin   = request.GET.get('checkin','')
    checkout  = request.GET.get('checkout','')
    adults    = request.GET.get('adult', 1)
    children  = request.GET.get('children', 0)
    available_rooms = Room.objects.filter(room_type=room_type, is_available=True)
    if not checkin or not checkout:
        messages.warning(request, "Please enter check-in and check-out dates to see availability.")
    sc = get_season_context()
    from decimal import Decimal
    context = {
        'hotel': hotel, 'room_type': room_type,
        'available_rooms': available_rooms,
        'checkin': checkin, 'checkout': checkout,
        'adults': adults, 'children': children,
        'seasonal_price': round(room_type.price * Decimal(str(sc['season_multiplier'])), 2),
    }
    context.update(sc)
    return render(request, 'hotel/room_type_detail.html', context)


def add_review(request, slug):
    hotel = get_object_or_404(Hotel, slug=slug)
    if not request.user.is_authenticated:
        messages.error(request, "Login to leave a review.")
        return redirect('accounts:login')
    if request.method == 'POST':
        has_stayed = False
        if request.user.is_authenticated:
            from guests.models import Reservation as GR
            has_stayed = GR.objects.filter(
                user=request.user, hotel=hotel, payment_status='paid').exists()
        if not has_stayed:
            messages.info(request, "Note: Reviews from verified stays are highlighted with a badge.")
        Review.objects.update_or_create(
            hotel=hotel, user=request.user,
            defaults={
                'rating': request.POST.get('rating', 3),
                'review': request.POST.get('review',''),
                'active': True,
            }
        )
        messages.success(request, "Review submitted!")
    return redirect('rooms:hotel_detail', slug=slug)


def compare_hotels(request):
    from django.http import JsonResponse
    ids = request.GET.getlist('ids')
    hotels = Hotel.objects.filter(id__in=ids, status='Live').prefetch_related('room_types', 'features')
    data = []
    for h in hotels[:2]:
        rts = h.hotel_room_types
        cheapest = rts.order_by('price').first()
        data.append({
            'id': h.id, 'name': h.name, 'city': h.city or '—', 'slug': h.slug,
            'rating': str(h.average_rating or '—'),
            'min_price': str(cheapest.price) if cheapest else '—',
            'room_types': rts.count(),
            'features': [f.name for f in h.features.all()[:5]],
        })
    return JsonResponse({'hotels': data})


def contact(request):
    sent = False
    form_data = {}
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        phone   = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', 'General Inquiry')
        message = request.POST.get('message', '').strip()
        if name and email and message:
            from django.core.mail import send_mail
            body = f"From: {name} <{email}>\nPhone: {phone}\n\nMessage:\n{message}"
            try:
                send_mail(
                    subject=f"[Red HMS Contact] {subject}",
                    message=body,
                    from_email=email,
                    recipient_list=['support@redhms.com'],
                    fail_silently=True,
                )
            except Exception:
                pass
            sent = True
        else:
            form_data = {'name': name, 'email': email, 'phone': phone, 'message': message}
    return render(request, 'hotel/contact.html', {'sent': sent, 'form_data': form_data})
