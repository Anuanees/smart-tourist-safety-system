from django.urls import path
from . import views

urlpatterns = [
    # Places CRUD
    path('add_place/', views.add_place, name='add_place'),
    path('edit_place/<int:place_id>/', views.edit_place, name='edit_place'),
    path('delete_place/<int:place_id>/', views.delete_place, name='delete_place'),

    # Danger Zones CRUD
    path('add_zone/', views.add_zone, name='add_zone'),
    path('edit_zone/<int:zone_id>/', views.edit_zone, name='edit_zone'),
    path('delete_zone/<int:zone_id>/', views.delete_zone, name='delete_zone'),
]
