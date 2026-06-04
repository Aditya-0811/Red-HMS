from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Reservation, Bookmark, Coupon, ActivityLog


class ActivityLogInline(admin.TabularInline):
    model      = ActivityLog
    extra      = 0
    readonly_fields = ['date']


@admin.register(Reservation)
class ReservationAdmin(ImportExportModelAdmin):
    inlines      = [ActivityLogInline]
    list_display = ['booking_id','full_name','hotel','room_type',
                    'check_in_date','check_out_date','total_days',
                    'total','payment_status','checked_in','checked_out','is_active']
    list_filter  = ['hotel','payment_status','is_active','checked_in','checked_out']
    search_fields = ['booking_id','full_name','email','phone']
    list_editable = ['is_active','checked_in','checked_out']
    readonly_fields = ['booking_id','success_id','date']
    list_per_page   = 50


@admin.register(Coupon)
class CouponAdmin(ImportExportModelAdmin):
    list_display  = ['code','hotel','discount_type','discount','redemption_limit',
                     'valid_from','valid_to','active']
    list_filter   = ['hotel','discount_type','active']
    list_editable = ['active']
    search_fields = ['code','hotel__name']
    list_per_page = 50


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display  = ['user','hotel','date']
    search_fields = ['user__username','hotel__name']
    list_per_page = 50


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ['reservation','staff','description','date']
    search_fields = ['reservation__booking_id','staff__username']
    list_per_page = 50
