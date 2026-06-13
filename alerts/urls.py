from django.urls import path
from . import views

urlpatterns = [
    path('api/nearby-data/', views.nearby_data, name='nearby_data'),
    path('api/send-sos/', views.send_sos, name='send_sos'),
    path('api/check-danger-zone/', views.check_danger_zone, name='check_danger_zone'),
]
