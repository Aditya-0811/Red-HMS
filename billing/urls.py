from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Checkout page (shows Stripe + PayPal buttons, handles coupon POST)
    path('payment/<str:booking_id>/',                      views.checkout_page,             name='payment'),
    path('checkout/<str:booking_id>/',                     views.checkout_page,             name='checkout_page'),

    # Stripe AJAX endpoint — called by Stripe.js fetch()
    path('api/checkout-session/<str:booking_id>/',         views.create_checkout_session,   name='api_checkout_session'),

    # Stripe Payment Element endpoints
    path('api/payment-intent/<str:booking_id>/',           views.stripe_payment_intent,     name='stripe_payment_intent'),
    path('stripe/return/<str:booking_id>/',                views.stripe_return,             name='stripe_return'),

    # Stripe redirect after payment
    path('success/<str:booking_id>/',                      views.payment_success,           name='payment_success'),
    path('failed/<str:booking_id>/',                       views.payment_failed,            name='payment_failed'),

    # PayPal redirect after approval
    path('paypal/success/<str:booking_id>/',               views.paypal_success,            name='paypal_success'),

    # Stripe Webhook (register this URL in Stripe Dashboard)
    path('webhook/stripe/',                                views.stripe_webhook,            name='stripe_webhook'),

    # Invoice
    path('invoice/<str:booking_id>/',                      views.invoice_view,              name='invoice'),

    # Demo card payment (simulated – no real gateway)
    path('demo/<str:booking_id>/',                         views.demo_payment,              name='demo_payment'),

    # Room status updater (called by JS setInterval every 60s)
    path('update-room-status/',                            views.update_room_status,        name='update_room_status'),
]
