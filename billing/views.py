"""
Red HMS – Billing Views
=======================
Implements:
  1. Stripe Checkout Session  (matches reference create_checkout_session exactly)
  2. PayPal SDK payment       (matches reference paypal.Buttons)
  3. Payment success/fail     (with anti-manipulation verification)
  4. Coupon application       (matches reference checkout coupon logic)
  5. Invoice view
  6. Room status updater      (cron-style, called by JS setInterval)
"""

import stripe
import json
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils import timezone

from guests.models import Reservation, Coupon
from accounts.models import Notification
from .models import Invoice, Payment


# ══════════════════════════════════════════════════════════
# CHECKOUT PAGE (with coupon support)
# Matches reference: hotel/checkout view
# ══════════════════════════════════════════════════════════

def checkout_page(request, booking_id):
    """
    Display the checkout/payment page.
    Handles coupon code POST requests.
    Shows Stripe, PayPal buttons.
    """
    reservation = get_object_or_404(Reservation, booking_id=booking_id)

    # If already paid, show the success page instead of dumping the user on the homepage
    if reservation.payment_status == "paid":
        messages.info(request, "This booking is already confirmed!")
        return render(request, "billing/payment_success.html", {
            "reservation": reservation,
            "rooms": reservation.room.all(),
        })

    # Allow retry after failure — reset to processing
    if reservation.payment_status in ("initiated", "failed"):
        reservation.payment_status = "processing"
        reservation.save()

    # ── Coupon application (matches reference exactly) ──
    now = timezone.now()
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                valid_from__lte=now,
                valid_to__gte=now,
                active=True,
            )

            # Check if already applied
            if coupon in reservation.coupons.all():
                messages.warning(request, "Coupon Already Activated")
                return redirect("billing:checkout_page", booking_id=reservation.booking_id)

            # Calculate discount
            if coupon.discount_type == "Percentage":
                discount = reservation.total * coupon.discount / 100
            else:
                discount = coupon.discount

            # Apply coupon
            reservation.coupons.add(coupon)
            reservation.total  -= discount
            reservation.saved  += discount
            reservation.save()

            messages.success(request, f"Coupon '{coupon.code}' applied! You saved ${discount:.2f}")
            return redirect("billing:checkout_page", booking_id=reservation.booking_id)

        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired coupon code.")
            return redirect("billing:checkout_page", booking_id=reservation.booking_id)

    context = {
        "reservation"         : reservation,
        "rooms"               : reservation.room.all(),
        "stripe_publishable_key": settings.STRIPE_PUBLIC_KEY,
        "paypal_client_id"    : settings.PAYPAL_CLIENT_ID,
        "website_address"     : settings.WEBSITE_ADDRESS,
    }
    return render(request, "billing/payment.html", context)


# ══════════════════════════════════════════════════════════
# STRIPE – Create Checkout Session (AJAX POST)
# Matches reference create_checkout_session exactly
# ══════════════════════════════════════════════════════════

@csrf_exempt
def create_checkout_session(request, booking_id):
    """
    Called by the Stripe.js frontend to create a checkout session.
    Returns JSON: { sessionId: '...' }
    """
    # The reference reads JSON body from the fetch() call
    try:
        request_data = json.loads(request.body)
    except Exception:
        request_data = {}

    reservation = get_object_or_404(Reservation, booking_id=booking_id)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email     = reservation.email,
            payment_method_types = ['card'],
            line_items = [
                {
                    'price_data': {
                        'currency'     : 'usd',
                        'product_data' : {
                            'name': f"Booking #{reservation.booking_id} – {reservation.hotel.name}",
                            'description': (
                                f"Room: {reservation.room_type.type} | "
                                f"Check-in: {reservation.check_in_date} | "
                                f"Check-out: {reservation.check_out_date} | "
                                f"{reservation.total_days} night(s)"
                            ),
                        },
                        'unit_amount': int(reservation.total * 100),  # Stripe uses cents
                    },
                    'quantity': 1,
                }
            ],
            mode = 'payment',
            # Success URL passes session_id, success_id, and booking_total for verification
            success_url = (
                request.build_absolute_uri(
                    reverse('billing:payment_success', args=[reservation.booking_id])
                )
                + "?session_id={CHECKOUT_SESSION_ID}"
                + "&success_id=" + str(reservation.success_id)
                + "&booking_total=" + str(reservation.total)
            ),
            cancel_url = (
                request.build_absolute_uri(
                    reverse('billing:payment_failed', args=[reservation.booking_id])
                )
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
        )

        # Save the Stripe session ID to the reservation
        reservation.payment_status         = "processing"
        reservation.stripe_payment_intent  = checkout_session['id']
        reservation.save()

        return JsonResponse({'sessionId': checkout_session.id})

    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════
# STRIPE WEBHOOK  (for server-side payment confirmation)
# ══════════════════════════════════════════════════════════

@csrf_exempt
def stripe_webhook(request):
    """
    Stripe sends events here after payment is processed.
    Verifies the webhook signature before processing.
    Register this URL at: https://dashboard.stripe.com/test/webhooks
    Endpoint URL: https://your-domain.com/billing/webhook/stripe/
    Event to listen for: checkout.session.completed
    """
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    if not webhook_secret:
        # No webhook secret configured — skip signature verification (development only)
        try:
            event = json.loads(payload)
        except Exception:
            return HttpResponse(status=400)
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            return HttpResponse('Invalid payload', status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse('Invalid signature', status=400)

    if event['type'] == 'checkout.session.completed':
        _fulfill_reservation_from_session(event['data']['object'])
    elif event['type'] == 'payment_intent.succeeded':
        _fulfill_from_payment_intent(event['data']['object'])

    return HttpResponse(status=200)


def _fulfill_reservation_from_session(session):
    try:
        reservation = Reservation.objects.get(stripe_payment_intent=session['id'])
        if reservation.payment_status != "paid":
            reservation.payment_status = "paid"
            reservation.save()
            _create_invoice_and_notify(reservation, payment_method='Stripe')
    except Reservation.DoesNotExist:
        pass


def _fulfill_from_payment_intent(pi):
    try:
        reservation = Reservation.objects.get(stripe_payment_intent=pi['id'])
        if reservation.payment_status != "paid":
            reservation.payment_status = "paid"
            reservation.save()
            _create_invoice_and_notify(reservation, payment_method='Stripe')
    except Reservation.DoesNotExist:
        pass


# ══════════════════════════════════════════════════════════
# PAYMENT SUCCESS  (Stripe redirect)
# Matches reference payment_success with anti-manipulation check
# ══════════════════════════════════════════════════════════

def payment_success(request, booking_id):
    """
    Stripe redirects here after successful payment.
    Verifies: success_id matches DB and booking_total matches DB.
    Anti-manipulation: if totals don't match, marks as failed.
    """
    success_id    = request.GET.get('success_id', '').rstrip('/')
    booking_total = request.GET.get('booking_total', '').rstrip('/')

    if success_id and booking_total:
        try:
            reservation = Reservation.objects.get(
                booking_id=booking_id,
                success_id=success_id
            )
        except Reservation.DoesNotExist:
            messages.error(request, "Booking not found.")
            return redirect("/")

        # ── Anti-manipulation verification (reference pattern) ──
        if Decimal(str(booking_total)) == reservation.total:

            if reservation.payment_status in ("processing", "initiated"):
                reservation.payment_status = "paid"
                reservation.save()

                # Create invoice, notification, send email
                _create_invoice_and_notify(reservation, payment_method='Stripe')

                from guests.models import ActivityLog
                ActivityLog.objects.create(
                    reservation=reservation, staff=None,
                    description=f"Payment confirmed · ${reservation.total} · #{reservation.booking_id}",
                )

                # Clear session cart
                if 'selection_data_obj' in request.session:
                    del request.session['selection_data_obj']

                messages.success(request, "Payment successful! Your booking is confirmed.")

            elif reservation.payment_status == "paid":
                messages.info(request, "This booking has already been paid for.")

            else:
                messages.error(request, "Something went wrong. Please contact support.")
                return redirect("/")
        else:
            # Total mismatch — payment manipulation detected
            messages.error(request, "Error: Payment Manipulation Detected. This payment has been cancelled.")
            reservation.payment_status = "failed"
            reservation.save()
            return redirect("/")

        context = {
            "reservation" : reservation,
            "rooms"       : reservation.room.all(),
        }
        return render(request, "billing/payment_success.html", context)

    else:
        # Missing params — payment manipulation
        messages.error(request, "Error: Payment Manipulation Detected. This payment has been cancelled.")
        try:
            reservation = Reservation.objects.get(booking_id=booking_id)
            reservation.payment_status = "failed"
            reservation.save()
        except Reservation.DoesNotExist:
            pass
        return redirect("/")


# ══════════════════════════════════════════════════════════
# PAYPAL SUCCESS  (PayPal onApprove redirect)
# Matches reference PayPal redirect URL pattern
# ══════════════════════════════════════════════════════════

def paypal_success(request, booking_id):
    """
    PayPal redirects here after payment approval.
    URL params: PayerID, success_id, booking_total
    """
    success_id    = request.GET.get('success_id', '').rstrip('/')
    booking_total = request.GET.get('booking_total', '').rstrip('/')
    payer_id      = request.GET.get('PayerID', '')

    if success_id and booking_total:
        try:
            reservation = Reservation.objects.get(
                booking_id=booking_id,
                success_id=success_id,
            )
        except Reservation.DoesNotExist:
            messages.error(request, "Booking not found.")
            return redirect("/")

        if reservation.payment_status in ("processing", "initiated"):
            reservation.payment_status = "paid"
            reservation.save()

            _create_invoice_and_notify(reservation, payment_method='PayPal')

            if 'selection_data_obj' in request.session:
                del request.session['selection_data_obj']

            messages.success(request, "PayPal payment successful! Your booking is confirmed.")

        context = {
            "reservation" : reservation,
            "rooms"       : reservation.room.all(),
        }
        return render(request, "billing/payment_success.html", context)

    messages.error(request, "Payment verification failed.")
    return redirect("/")


# ══════════════════════════════════════════════════════════
# PAYMENT FAILED
# ══════════════════════════════════════════════════════════

def payment_failed(request, booking_id):
    """Called when Stripe redirects to cancel_url or payment fails."""
    reservation = get_object_or_404(Reservation, booking_id=booking_id)
    reservation.payment_status = "failed"
    reservation.save()
    messages.error(request, "Payment failed or was cancelled.")
    return render(request, "billing/payment_failed.html", {"reservation": reservation})


# ══════════════════════════════════════════════════════════
# DEMO PAYMENT  (simulated card payment – no real gateway)
# ══════════════════════════════════════════════════════════

def demo_payment(request, booking_id):
    """
    Simulated card payment for demo/testing.
    Card 4000000000000002 → fail; all others → success.
    """
    reservation = get_object_or_404(Reservation, booking_id=booking_id)

    if reservation.payment_status == "paid":
        messages.info(request, "This booking is already paid.")
        return render(request, "billing/payment_success.html", {
            "reservation": reservation,
            "rooms": reservation.room.all(),
        })

    if request.method != "POST":
        return redirect('billing:payment', booking_id=booking_id)

    card_number = request.POST.get('card_number', '').replace(' ', '').replace('-', '')

    # Simulate failure for the canonical "decline" test card
    if card_number == '4000000000000002':
        reservation.payment_status = "failed"
        reservation.save()
        messages.error(request, "Your card was declined. Please try a different card.")
        return render(request, "billing/payment_failed.html", {"reservation": reservation})

    # All other cards → success
    if reservation.payment_status in ("processing", "initiated"):
        reservation.payment_status = "paid"
        reservation.save()
        _create_invoice_and_notify(reservation, payment_method='Cash')
        if 'selection_data_obj' in request.session:
            del request.session['selection_data_obj']

    messages.success(request, "Payment successful! Your booking is confirmed.")
    return render(request, "billing/payment_success.html", {
        "reservation": reservation,
        "rooms": reservation.room.all(),
    })


# ══════════════════════════════════════════════════════════
# INVOICE
# ══════════════════════════════════════════════════════════

def invoice_view(request, booking_id):
    reservation = get_object_or_404(Reservation, booking_id=booking_id)
    return render(request, "billing/invoice.html", {
        "reservation" : reservation,
        "rooms"       : reservation.room.all(),
        "invoice"     : getattr(reservation, "invoice", None),
    })


# ══════════════════════════════════════════════════════════
# ROOM STATUS UPDATER  (called every 60s by JS setInterval)
# Matches reference update_room_status exactly
# ══════════════════════════════════════════════════════════

@csrf_exempt
def update_room_status(request):
    """
    Updates room availability based on today's date.
    Called automatically every 60 seconds by red_hms_custom.js.
    """
    today = timezone.now().date()

    for reservation in Reservation.objects.filter(is_active=True, payment_status="paid"):

        if not reservation.checked_in_tracker:
            if reservation.check_in_date > today:
                reservation.checked_in_tracker = False
                reservation.save()
                for room in reservation.room.all():
                    room.is_available = True
                    room.save()
            else:
                reservation.checked_in_tracker = True
                reservation.save()
                for room in reservation.room.all():
                    room.is_available = False
                    room.save()
        else:
            if reservation.check_out_date > today:
                reservation.checked_out_tracker = False
                reservation.save()
                for room in reservation.room.all():
                    room.is_available = False
                    room.save()
            else:
                reservation.checked_out_tracker = True
                reservation.save()
                for room in reservation.room.all():
                    room.is_available = True
                    room.save()

    return HttpResponse(today)


# ══════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ══════════════════════════════════════════════════════════

def _create_invoice_and_notify(reservation, payment_method='Stripe'):
    """Create invoice, payment record, notification, and send confirmation email."""
    from .models import Payment

    # Create Invoice
    Invoice.objects.get_or_create(
        reservation=reservation,
        defaults={
            "subtotal": reservation.before_discount,
            "discount": reservation.saved,
            "total"   : reservation.total,
        }
    )

    # Create Payment record (idempotent — skip if one already exists for this reservation)
    Payment.objects.get_or_create(
        reservation=reservation,
        defaults={
            "amount": reservation.total,
            "method": payment_method,
            "status": "paid",
            "stripe_payment_intent": reservation.stripe_payment_intent or '',
        }
    )

    # Create Notification
    if reservation.user:
        Notification.objects.create(
            user    = reservation.user,
            type    = "Booking Confirmed",
            message = (
                f"Your booking #{reservation.booking_id} at "
                f"{reservation.hotel.name} is confirmed. "
                f"Check-in: {reservation.check_in_date}."
            ),
        )

    # Send confirmation email
    _send_confirmation_email(reservation)


def _send_confirmation_email(reservation):
    """Send HTML + plain-text booking confirmation email."""
    try:
        merge = {
            "reservation" : reservation,
            "rooms"       : reservation.room.all(),
            "full_name"   : reservation.full_name,
        }
        subject   = f"Booking Confirmed – #{reservation.booking_id} | Red HMS"
        text_body = render_to_string("email/booking_confirmed.txt",  merge)
        html_body = render_to_string("email/booking_confirmed.html", merge)

        msg = EmailMultiAlternatives(
            subject    = subject,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [reservation.email],
            body       = text_body,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
    except Exception as e:
        print(f"[Red HMS Email Error] {e}")


# ══════════════════════════════════════════════════════════
# STRIPE PAYMENT ELEMENT  (embedded on-page card form)
# ══════════════════════════════════════════════════════════

@csrf_exempt
def stripe_payment_intent(request, booking_id):
    """Create a PaymentIntent and return its client_secret for Payment Element."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    reservation = get_object_or_404(Reservation, booking_id=booking_id)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(reservation.total * 100),
            currency='usd',
            receipt_email=reservation.email,
            metadata={
                'booking_id': booking_id,
                'success_id': str(reservation.success_id),
            },
        )
        reservation.stripe_payment_intent = intent.id
        reservation.save(update_fields=['stripe_payment_intent'])
        return JsonResponse({'clientSecret': intent.client_secret})
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def stripe_return(request, booking_id):
    """Handle Stripe Payment Element return_url redirect."""
    redirect_status    = request.GET.get('redirect_status', '')
    payment_intent_id  = request.GET.get('payment_intent', '')

    try:
        reservation = Reservation.objects.get(booking_id=booking_id)
    except Reservation.DoesNotExist:
        messages.error(request, "Booking not found.")
        return redirect("/")

    if redirect_status == 'succeeded':
        if reservation.payment_status != 'paid':
            reservation.payment_status = 'paid'
            reservation.save()
            _create_invoice_and_notify(reservation, payment_method='Stripe')
            from guests.models import ActivityLog
            ActivityLog.objects.create(
                reservation=reservation, staff=None,
                description=f"Payment confirmed via Stripe · ${reservation.total} · #{booking_id}",
            )
            if 'selection_data_obj' in request.session:
                del request.session['selection_data_obj']
        messages.success(request, "Payment successful! Your booking is confirmed.")
        return render(request, 'billing/payment_success.html', {
            'reservation': reservation,
            'rooms': reservation.room.all(),
        })

    messages.error(request, "Payment was not completed. Please try again.")
    if reservation.payment_status not in ('paid',):
        reservation.payment_status = 'failed'
        reservation.save()
    return render(request, 'billing/payment_failed.html', {'reservation': reservation})
