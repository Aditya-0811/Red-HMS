from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Invoice, Payment, RoomService


class RoomServiceInline(admin.TabularInline):
    model = RoomService
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(ImportExportModelAdmin):
    list_display    = ['invoice_id','reservation','subtotal','discount','tax','total','issued_date']
    search_fields   = ['invoice_id','reservation__booking_id','reservation__full_name']
    readonly_fields = ['invoice_id','issued_date']
    list_per_page   = 50


@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    list_display    = ['payment_id','reservation','amount','method','status','date']
    list_filter     = ['method','status']
    search_fields   = ['payment_id','reservation__booking_id']
    list_editable   = ['status']
    readonly_fields = ['payment_id','date']
    list_per_page   = 50


@admin.register(RoomService)
class RoomServiceAdmin(ImportExportModelAdmin):
    list_display  = ['reservation','room','service_type','price','date']
    list_filter   = ['service_type']
    search_fields = ['reservation__booking_id']
    list_per_page = 50
