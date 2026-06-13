# accounts/urls.py

from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('', views.index, name='index'),

    # Single unified login
    path('login/', views.login_view, name='login'),
    path('tourist-signup/', views.tourist_signup, name='tourist_signup'),
    path('tourist-dashboard/', views.tourist_dashboard, name='tourist_dashboard'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin Management Pages
    path('admin/manage-places/', views.manage_places, name='manage_places'),
    path('admin/manage-zones/', views.manage_zones, name='manage_zones'),
    path('admin/manage-sos/', views.manage_sos, name='manage_sos'),
    path('admin/bulk-upload/', views.bulk_upload, name='bulk_upload'),
    
    # Admin Monitoring System
    path('admin-monitoring/', admin_views.admin_monitoring, name='admin_monitoring'),
    path('admin/api/live-tourists/', admin_views.api_live_tourists, name='api_live_tourists'),
    path('admin/api/tourist-detail/<int:tourist_id>/', admin_views.api_tourist_detail, name='api_tourist_detail'),
    path('admin/api/delete-tourist/<int:tourist_id>/', admin_views.api_delete_tourist, name='api_delete_tourist'),
    path('admin/api/live-sos/', admin_views.api_live_sos, name='api_live_sos'),
    path('admin/api/danger-zones/', admin_views.api_danger_zones, name='api_danger_zones'),
    path('admin/api/help-centers/', admin_views.api_help_centers, name='api_help_centers'),
    path('admin/api/update-sos-status/', admin_views.api_update_sos_status, name='api_update_sos_status'),
    path('admin/api/dashboard-stats/', admin_views.api_dashboard_stats, name='api_dashboard_stats'),

    # Add Place & Zone
    path('add-place/', views.add_place, name='add_place'),
    path('add-zone/', views.add_zone, name='add_zone'),

    # Delete
    path('delete-place/<int:id>/', views.delete_place, name='delete_place'),
    path('delete-zone/<int:id>/', views.delete_zone, name='delete_zone'),

    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
]
