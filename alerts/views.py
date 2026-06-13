from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.models import DangerZone, Place
from alerts.models import SOSAlert
from alerts.utils import haversine_distance
import json


@login_required
def nearby_data(request):
    """
    API endpoint to fetch nearby danger zones and help centers
    based on tourist's current location.
    """
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
        radius_km = 5  # 5km radius
        
        # Get all danger zones
        zones = DangerZone.objects.all()
        nearby_zones = []
        
        for zone in zones:
            distance = haversine_distance(lat, lon, zone.latitude, zone.longitude)
            if distance <= radius_km:
                nearby_zones.append({
                    'id': zone.id,
                    'name': zone.name,
                    'risk_type': zone.risk_type,
                    'severity': zone.severity,
                    'latitude': float(zone.latitude),
                    'longitude': float(zone.longitude),
                    'distance': distance,
                    'additional_details': zone.additional_details
                })
        
        # Get all help centers
        places = Place.objects.all()
        nearby_places = []
        
        for place in places:
            if place.latitude and place.longitude:
                distance = haversine_distance(lat, lon, place.latitude, place.longitude)
                nearby_places.append({
                    'id': place.id,
                    'name': place.name,
                    'type': place.type,
                    'latitude': float(place.latitude),
                    'longitude': float(place.longitude),
                    'distance': distance,
                    'description': place.description
                })
        
        # Sort by distance
        nearby_zones.sort(key=lambda x: x['distance'])
        nearby_places.sort(key=lambda x: x['distance'])
        
        return JsonResponse({
            'status': 'success',
            'zones': nearby_zones,
            'places': nearby_places
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def send_sos(request):
    """
    API endpoint to handle SOS emergency alerts.
    Finds nearest police station or hospital and saves SOS alert.
    """
    try:
        data = json.loads(request.body)
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        
        # Get police stations and hospitals
        help_centers = Place.objects.filter(type__in=['Police Station', 'Hospital'])
        
        nearest_center = None
        min_distance = float('inf')
        
        for center in help_centers:
            if center.latitude and center.longitude:
                distance = haversine_distance(lat, lon, center.latitude, center.longitude)
                if distance < min_distance:
                    min_distance = distance
                    nearest_center = center
        
        # Create SOS Alert
        sos = SOSAlert.objects.create(
            tourist=request.user,
            latitude=lat,
            longitude=lon,
            nearest_help_center=nearest_center.name if nearest_center else 'None',
            distance_km=min_distance if nearest_center else None,
            status='pending'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'SOS Alert Sent Successfully!',
            'nearest_center': nearest_center.name if nearest_center else 'None',
            'distance': min_distance if nearest_center else 0,
            'sos_id': sos.id
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def check_danger_zone(request):
    """
    API endpoint to check if user is inside any danger zone geofence.
    Uses Haversine distance and configurable radius per zone.
    """
    try:
        data = json.loads(request.body)
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        
        # Get all danger zones
        zones = DangerZone.objects.all()
        
        for zone in zones:
            # Calculate distance in meters
            distance_km = haversine_distance(lat, lon, zone.latitude, zone.longitude)
            distance_meters = distance_km * 1000
            
            # Check if inside geofence radius
            if distance_meters <= zone.radius:
                return JsonResponse({
                    'inside': True,
                    'zone_id': zone.id,
                    'zone_name': zone.name,
                    'severity': zone.severity,
                    'risk_type': zone.risk_type,
                    'distance': round(distance_meters, 0),
                    'distance_km': round(distance_km, 2),
                    'message': f'You have entered a {zone.severity} Risk Area',
                    'additional_details': zone.additional_details
                })
        
        # Not inside any zone
        return JsonResponse({
            'inside': False
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
