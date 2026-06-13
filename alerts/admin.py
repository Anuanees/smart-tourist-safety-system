from django.contrib import admin
from .models import Alert, SOSAlert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['message', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['message']


@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = ['tourist', 'latitude', 'longitude', 'nearest_help_center', 'distance_km', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['tourist__username', 'nearest_help_center']
    readonly_fields = ['created_at']
