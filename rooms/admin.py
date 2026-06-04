from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Hotel, HotelGallery, HotelFeature, HotelFAQ, RoomType, Room, Review


class HotelGalleryInline(admin.TabularInline):
    model = HotelGallery
    extra = 1

class HotelFeatureInline(admin.TabularInline):
    model = HotelFeature
    extra = 1

class HotelFAQInline(admin.TabularInline):
    model = HotelFAQ
    extra = 1

class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 1

class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


@admin.register(Hotel)
class HotelAdmin(ImportExportModelAdmin):
    inlines           = [HotelGalleryInline, HotelFeatureInline, HotelFAQInline, RoomTypeInline]
    list_display      = ['thumbnail','name','user','city','status','featured','views']
    list_filter       = ['status','featured']
    list_editable     = ['status','featured']
    search_fields     = ['name','user__username','city']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page     = 50


@admin.register(RoomType)
class RoomTypeAdmin(ImportExportModelAdmin):
    inlines           = [RoomInline]
    list_display      = ['hotel','type','price','number_of_beds']
    list_filter       = ['hotel','type']
    prepopulated_fields = {'slug': ('type',)}
    list_per_page     = 50


@admin.register(Room)
class RoomAdmin(ImportExportModelAdmin):
    list_display  = ['room_number','hotel','room_type','price','is_available']
    list_filter   = ['hotel','room_type','is_available']
    list_editable = ['is_available']
    search_fields = ['room_number','hotel__name']
    list_per_page = 100


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['hotel','user','rating','active','date']
    list_filter   = ['rating','active']
    list_editable = ['active']
    list_per_page = 50
