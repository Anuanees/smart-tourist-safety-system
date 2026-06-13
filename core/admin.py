from django.contrib import admin
from .models import Place, DangerZone

# --- Place Admin ---
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'latitude', 'longitude', 'description')
    search_fields = ('name', 'type')
    list_filter = ('type',)

# --- DangerZone Admin ---
class DangerZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_type', 'severity', 'latitude', 'longitude', 'additional_details')
    search_fields = ('name', 'risk_type', 'severity')
    list_filter = ('risk_type', 'severity')

admin.site.register(Place, PlaceAdmin)
admin.site.register(DangerZone, DangerZoneAdmin)
