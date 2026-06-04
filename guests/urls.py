from django.urls import path
from . import views

app_name = 'guests'

urlpatterns = [
    # AJAX – matches reference custom.js exact URLs
    path('add_to_selection/',        views.add_to_selection,   name='add_to_selection'),
    path('delete_selection/',        views.delete_selection,   name='delete_selection'),
    path('delete_session/',          views.delete_session,     name='delete_session'),
    path('add_to_bookmark/',         views.add_to_bookmark,    name='add_to_bookmark'),

    # Pages
    path('selected-rooms/',          views.selected_rooms,     name='selected_rooms'),
    path('checkout/',                views.selected_rooms,     name='checkout'),
    path('bookmark/<slug:slug>/',    views.toggle_bookmark,    name='toggle_bookmark'),
    path('delete-bookmark/<int:bid>/',views.delete_bookmark,   name='delete_bookmark'),
    path('wishlist/',                views.wishlist_view,      name='wishlist'),
    path('my-reservations/',         views.my_reservations,    name='my_reservations'),
    path('reservation/<str:booking_id>/room-service/', views.request_room_service, name='room_service'),
    path('reservation/<str:booking_id>/modify/', views.modification_request, name='modification_request'),
    path('reservation/<str:booking_id>/', views.reservation_detail, name='reservation_detail'),
]
