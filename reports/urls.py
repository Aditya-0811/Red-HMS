from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/',              views.dashboard,          name='dashboard'),
    path('booking-detail/<str:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/',               views.all_bookings,       name='all_bookings'),
    path('bookings/export/',        views.export_bookings_csv, name='export_bookings_csv'),
    path('bookings/<str:booking_id>/email/', views.send_booking_email, name='send_booking_email'),
    path('bookings/<str:booking_id>/notes/', views.booking_notes,      name='booking_notes'),
    path('toggle-checkin/<str:booking_id>/', views.toggle_checkin,     name='toggle_checkin'),
    path('room-status/update/',     views.update_room_housekeeping,    name='room_status_update'),
    path('revenue/',                views.revenue_report,     name='revenue_report'),
    path('occupancy/',              views.occupancy_report,   name='occupancy_report'),
    path('wallet/',                 views.wallet,             name='wallet'),
    path('wallet/topup/',           views.wallet_topup,       name='wallet_topup'),
    path('notifications/',          views.notifications,      name='notifications'),
    path('generate/',               views.generate_report,    name='generate_report'),
]
