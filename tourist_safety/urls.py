from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),           # Homepage remains index.html
    path('core/', include('core.urls')),         # Places & zones CRUD
    path('accounts/', include('accounts.urls')), # Admin & Tourist accounts
    path('', include('alerts.urls')),            # Alerts API endpoints (existing)
    path('api/', include('api.urls')),           # ← NEW: REST API for Flutter
]

