# api/views.py

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Place, DangerZone
from alerts.models import SOSAlert
from alerts.utils import haversine_distance

from .serializers import (
    UserSerializer,
    PlaceSerializer,
    DangerZoneSerializer,
    SOSAlertSerializer,
    ChangePasswordSerializer,
    RegisterSerializer,
)


# ─────────────────────────────────────────────────────────
# HELPER — generate JWT token pair for a user
# ─────────────────────────────────────────────────────────
def _get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ─────────────────────────────────────────────────────────
# POST /api/login/
# Body: { "username": "...", "password": "..." }
# Returns: access + refresh tokens, user info
# ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    from django.contrib.auth import authenticate
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    tokens = _get_tokens(user)
    return Response({
        'message': 'Login successful.',
        'user': UserSerializer(user).data,
        'tokens': tokens,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# POST /api/register/
# Body: { "username": "...", "email": "...", "password": "..." }
# Creates a tourist account and returns tokens (auto-login)
# ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = _get_tokens(user)
        return Response({
            'message': 'Tourist account created successfully.',
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────
# POST /api/logout/
# Header: Authorization: Bearer <access_token>
# Body:   { "refresh": "<refresh_token>" }
# Blacklists the refresh token
# ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
    except Exception:
        # Even if blacklist fails, treat logout as successful
        return Response({'message': 'Logged out.'}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# GET /api/profile/
# Header: Authorization: Bearer <access_token>
# Returns current user profile
# ─────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# POST /api/change-password/
# Header: Authorization: Bearer <access_token>
# Body: { "old_password": "...", "new_password": "..." }
# ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        # Re-issue fresh tokens so Flutter doesn't get logged out
        tokens = _get_tokens(user)
        return Response({
            'message': 'Password changed successfully.',
            'tokens': tokens,
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────
# GET /api/danger-zones/
# Header: Authorization: Bearer <access_token>
# Returns all danger zones (tourist + admin)
# ─────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_danger_zones(request):
    zones = DangerZone.objects.all().order_by('id')
    serializer = DangerZoneSerializer(zones, many=True)
    return Response({
        'count': zones.count(),
        'danger_zones': serializer.data,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# GET /api/places/
# Header: Authorization: Bearer <access_token>
# Returns all places (tourist + admin)
# ─────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_places(request):
    places = Place.objects.all().order_by('id')
    serializer = PlaceSerializer(places, many=True)
    return Response({
        'count': places.count(),
        'places': serializer.data,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# GET /api/help-centers/
# Header: Authorization: Bearer <access_token>
# Optional query params: ?lat=...&lon=...&radius_km=5
# Returns places sorted by distance if coords provided
# ─────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_help_centers(request):
    places = Place.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).order_by('id')

    lat_str = request.GET.get('lat')
    lon_str = request.GET.get('lon')

    if lat_str and lon_str:
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            radius_km = float(request.GET.get('radius_km', 10))

            result = []
            for place in places:
                dist = haversine_distance(lat, lon, float(place.latitude), float(place.longitude))
                if dist <= radius_km:
                    data = PlaceSerializer(place).data
                    data['distance_km'] = round(dist, 2)
                    result.append(data)

            result.sort(key=lambda x: x['distance_km'])
            return Response({'count': len(result), 'help_centers': result}, status=status.HTTP_200_OK)

        except (ValueError, TypeError) as e:
            return Response({'error': f'Invalid coordinates: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = PlaceSerializer(places, many=True)
    return Response({
        'count': places.count(),
        'help_centers': serializer.data,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# GET  /api/sos/         → list tourist's own SOS history
# POST /api/sos/         → send a new SOS alert
# ─────────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_sos(request):

    # ── GET: return this tourist's SOS history ──
    if request.method == 'GET':
        sos_list = SOSAlert.objects.filter(tourist=request.user).order_by('-created_at')
        serializer = SOSAlertSerializer(sos_list, many=True)
        return Response({
            'count': sos_list.count(),
            'sos_history': serializer.data,
        }, status=status.HTTP_200_OK)

    # ── POST: create new SOS alert ──
    try:
        lat = float(request.data.get('lat') or request.data.get('latitude'))
        lon = float(request.data.get('lon') or request.data.get('longitude'))
    except (TypeError, ValueError):
        return Response(
            {'error': 'Valid lat and lon are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Find nearest police station or hospital
    help_centers = Place.objects.filter(
        type__in=['Police Station', 'Hospital'],
        latitude__isnull=False,
        longitude__isnull=False
    )
    nearest_center = None
    min_distance = float('inf')

    for center in help_centers:
        dist = haversine_distance(lat, lon, float(center.latitude), float(center.longitude))
        if dist < min_distance:
            min_distance = dist
            nearest_center = center

    sos = SOSAlert.objects.create(
        tourist=request.user,
        latitude=lat,
        longitude=lon,
        nearest_help_center=nearest_center.name if nearest_center else 'None',
        distance_km=round(min_distance, 2) if nearest_center else None,
        status='pending'
    )

    return Response({
        'message': 'SOS Alert sent successfully.',
        'sos_id': sos.id,
        'nearest_help_center': nearest_center.name if nearest_center else 'None',
        'distance_km': round(min_distance, 2) if nearest_center else None,
    }, status=status.HTTP_201_CREATED)

# ─────────────────────────────────────────────────────────
# POST /api/location/
# Header: Authorization: Bearer <access_token>
# Body:   { "lat": 12.345, "lon": 67.890 }
# Saves tourist GPS location to TouristLocation table.
# Added for Phase 1 — does NOT touch any existing view.
# ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_location(request):
    from core.models import TouristLocation
    try:
        lat = float(request.data.get('lat') or request.data.get('latitude'))
        lon = float(request.data.get('lon') or request.data.get('longitude'))
    except (TypeError, ValueError):
        return Response(
            {'error': 'Valid lat and lon are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    TouristLocation.objects.create(
        tourist=request.user,
        latitude=lat,
        longitude=lon,
    )
    return Response({'message': 'Location saved.'}, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────
# GET /api/admin/tourists/
# Header: Authorization: Bearer <access_token>  (admin only)
# Returns each tourist with their latest GPS coordinates.
# Added for Phase 1 — does NOT touch any existing view.
# ─────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_admin_tourists(request):
    from core.models import TouristLocation
    from django.contrib.auth.models import User

    tourists = User.objects.filter(is_superuser=False).order_by('username')
    result = []
    for t in tourists:
        latest = t.locations.first()  # ordered by -timestamp in Meta
        result.append({
            'id':        t.id,
            'username':  t.username,
            'email':     t.email,
            'last_location': {
                'latitude':  float(latest.latitude)  if latest else None,
                'longitude': float(latest.longitude) if latest else None,
                'timestamp': latest.timestamp.isoformat() if latest else None,
            }
        })
    return Response({
        'count': len(result),
        'tourists': result,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# GET /api/admin/sos/
# Header: Authorization: Bearer <access_token>  (admin only)
# Returns ALL SOS alerts across all tourists.
# Added for Phase 1 — does NOT touch any existing view.
# ─────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_admin_sos(request):
    from .serializers import SOSAlertSerializer
    all_sos = SOSAlert.objects.all().order_by('-created_at')
    serializer = SOSAlertSerializer(all_sos, many=True)
    return Response({
        'count': all_sos.count(),
        'sos_alerts': serializer.data,
    }, status=status.HTTP_200_OK)
