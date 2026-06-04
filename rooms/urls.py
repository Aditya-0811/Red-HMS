from django.urls import path
from . import views

app_name = 'rooms'

urlpatterns = [
    path('',                                            views.index,            name='index'),
    path('hotels/',                                     views.hotel_listing,    name='hotel_listing'),
    path('hotels/count/',                               views.hotel_count_ajax,  name='hotel_count_ajax'),
    path('hotels/compare/',                             views.compare_hotels,    name='compare_hotels'),
    path('hotels/<slug:slug>/',                         views.hotel_detail,     name='hotel_detail'),
    path('hotels/<slug:slug>/room/<slug:rt_slug>/',     views.room_type_detail, name='room_type_detail'),
    path('hotels/<slug:slug>/review/',                  views.add_review,       name='add_review'),
    path('contact/',                                    views.contact,          name='contact'),
]
