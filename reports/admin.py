from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display    = ['title','report_type','generated_by','data_from','data_to','generated_at']
    list_filter     = ['report_type']
    search_fields   = ['title']
    readonly_fields = ['generated_at']
    list_per_page   = 50
