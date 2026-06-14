# api/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────
    path('login/',           views.api_login,           name='api_login'),
    path('logout/',          views.api_logout,          name='api_logout'),
    path('register/',        views.api_register,        name='api_register'),
    path('token/refresh/',   TokenRefreshView.as_view(), name='api_token_refresh'),

    # ── User ──────────────────────────────────
    path('profile/',         views.api_profile,         name='api_profile'),
    path('change-password/', views.api_change_password, name='api_change_password'),

    # ── Data ──────────────────────────────────
    path('danger-zones/',    views.api_danger_zones,    name='api_danger_zones_list'),
    path('places/',          views.api_places,          name='api_places_list'),
    path('help-centers/',    views.api_help_centers,    name='api_help_centers_list'),
    path('sos/',             views.api_sos,             name='api_sos'),

    # ── Phase 1: Location tracking & Admin views ──
    path('location/',                views.api_location,              name='api_location'),
    path('admin/tourists/',          views.api_admin_tourists,        name='api_admin_tourists'),
    path('admin/sos/',               views.api_admin_sos,             name='api_admin_sos'),
    path('admin/tourists/<int:user_id>/', views.api_admin_delete_tourist, name='api_admin_delete_tourist'),
    path('admin/sos/<int:sos_id>/',      views.api_admin_sos_update,     name='api_admin_sos_update'),
]
