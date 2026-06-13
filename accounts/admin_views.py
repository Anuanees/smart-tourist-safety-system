# accounts/admin_views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import Place, DangerZone
from alerts.models import SOSAlert
from alerts.utils import haversine_distance
import json


def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_superuser


# ─────────────────────────────────────────
# ADMIN MONITORING PAGE
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def admin_monitoring(request):
    """Main admin monitoring dashboard view"""
    context = {
        'total_tourists': User.objects.filter(is_superuser=False).count(),
        'total_danger_zones': DangerZone.objects.count(),
        'total_help_centers': Place.objects.count(),
    }
    return render(request, 'accounts/admin_monitoring.html', context)


# ─────────────────────────────────────────
# API: LIVE TOURISTS
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_live_tourists(request):
    """Return all tourists with their latest known location from SOS history."""
    try:
        tourists = User.objects.filter(is_superuser=False)
        tourist_data = []

        for tourist in tourists:
            latest_sos = SOSAlert.objects.filter(tourist=tourist).order_by('-created_at').first()

            if latest_sos:
                lat = float(latest_sos.latitude)
                lon = float(latest_sos.longitude)

                # Danger zone check
                in_danger = False
                for zone in DangerZone.objects.all():
                    dist = haversine_distance(lat, lon, zone.latitude, zone.longitude) * 1000
                    if dist <= zone.radius:
                        in_danger = True
                        break

                if latest_sos.status == 'pending':
                    status = 'sos'
                elif in_danger:
                    status = 'danger'
                else:
                    status = 'safe'

                # Determine if active session exists
                is_active = _has_active_session(tourist)

                tourist_data.append({
                    'id': tourist.id,
                    'username': tourist.username,
                    'name': tourist.get_full_name() or tourist.username,
                    'email': tourist.email or '—',
                    'first_name': tourist.first_name or '—',
                    'last_name': tourist.last_name or '—',
                    'date_joined': tourist.date_joined.strftime('%d %b %Y'),
                    'last_login': tourist.last_login.strftime('%d %b %Y %H:%M') if tourist.last_login else '—',
                    'is_active': tourist.is_active,
                    'session_active': is_active,
                    'latitude': lat,
                    'longitude': lon,
                    'status': status,
                    'last_update': latest_sos.created_at.isoformat(),
                    'last_update_ago': get_time_ago(latest_sos.created_at),
                    'nearest_help_center': latest_sos.nearest_help_center or '—',
                    'sos_count': SOSAlert.objects.filter(tourist=tourist).count(),
                })

        return JsonResponse({'status': 'success', 'tourists': tourist_data})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# API: TOURIST DETAIL
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_tourist_detail(request, tourist_id):
    """Return full detail for a single tourist."""
    try:
        tourist = User.objects.get(id=tourist_id, is_superuser=False)

        # Last 5 SOS alerts as activity history
        sos_history = SOSAlert.objects.filter(tourist=tourist).order_by('-created_at')[:5]
        activity = []
        for sos in sos_history:
            activity.append({
                'type': 'SOS Alert',
                'status': sos.status,
                'latitude': float(sos.latitude),
                'longitude': float(sos.longitude),
                'nearest_help_center': sos.nearest_help_center or '—',
                'distance_km': float(sos.distance_km) if sos.distance_km else 0,
                'time': sos.created_at.strftime('%d %b %Y %H:%M:%S'),
                'time_ago': get_time_ago(sos.created_at),
            })

        latest_sos = SOSAlert.objects.filter(tourist=tourist).order_by('-created_at').first()

        data = {
            'id': tourist.id,
            'username': tourist.username,
            'full_name': tourist.get_full_name() or '—',
            'first_name': tourist.first_name or '—',
            'last_name': tourist.last_name or '—',
            'email': tourist.email or '—',
            'date_joined': tourist.date_joined.strftime('%d %b %Y, %H:%M'),
            'last_login': tourist.last_login.strftime('%d %b %Y, %H:%M') if tourist.last_login else 'Never',
            'is_active': tourist.is_active,
            'session_active': _has_active_session(tourist),
            'sos_count': SOSAlert.objects.filter(tourist=tourist).count(),
            'last_location': {
                'latitude': float(latest_sos.latitude) if latest_sos else None,
                'longitude': float(latest_sos.longitude) if latest_sos else None,
                'time_ago': get_time_ago(latest_sos.created_at) if latest_sos else '—',
            },
            'activity_history': activity,
        }
        return JsonResponse({'status': 'success', 'tourist': data})

    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Tourist not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# API: DELETE TOURIST
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_delete_tourist(request, tourist_id):
    """Permanently delete a tourist account, all their sessions and activity records."""
    if request.method != 'DELETE':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)

    try:
        tourist = User.objects.get(id=tourist_id, is_superuser=False)
        username = tourist.username

        # Delete related SOS records (CASCADE handles it, but explicit for clarity)
        SOSAlert.objects.filter(tourist=tourist).delete()

        # Invalidate all sessions belonging to this user
        _clear_user_sessions(tourist)

        # Hard-delete the user
        tourist.delete()

        return JsonResponse({
            'status': 'success',
            'message': f'Tourist "{username}" has been permanently deleted.'
        })

    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Tourist not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# API: LIVE SOS
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_live_sos(request):
    """Return all SOS alerts from today (most recent first)."""
    try:
        today = timezone.now().date()
        sos_alerts = SOSAlert.objects.filter(created_at__date=today).order_by('-created_at')

        sos_data = []
        for sos in sos_alerts:
            sos_data.append({
                'id': sos.id,
                'tourist_id': sos.tourist.id,
                'tourist_name': sos.tourist.get_full_name() or sos.tourist.username,
                'tourist_username': sos.tourist.username,
                'tourist_email': sos.tourist.email or '—',
                'latitude': float(sos.latitude),
                'longitude': float(sos.longitude),
                'nearest_help_center': sos.nearest_help_center or '—',
                'distance_km': float(sos.distance_km) if sos.distance_km else 0,
                'status': sos.status,
                'created_at': sos.created_at.strftime('%d %b %Y, %H:%M:%S'),
                'time_ago': get_time_ago(sos.created_at),
            })

        return JsonResponse({'status': 'success', 'sos_alerts': sos_data})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# API: DANGER ZONES
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_danger_zones(request):
    try:
        zones = DangerZone.objects.all()
        zone_data = [{
            'id': z.id,
            'name': z.name,
            'latitude': float(z.latitude),
            'longitude': float(z.longitude),
            'radius': z.radius,
            'severity': z.severity,
            'risk_type': z.risk_type,
            'additional_details': z.additional_details,
        } for z in zones]
        return JsonResponse({'status': 'success', 'danger_zones': zone_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# API: HELP CENTERS
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_help_centers(request):
    try:
        places = Place.objects.filter(latitude__isnull=False, longitude__isnull=False)
        place_data = [{
            'id': p.id,
            'name': p.name,
            'type': p.type,
            'latitude': float(p.latitude),
            'longitude': float(p.longitude),
            'description': p.description,
        } for p in places]
        return JsonResponse({'status': 'success', 'help_centers': place_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# API: UPDATE SOS STATUS
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_update_sos_status(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    try:
        data = json.loads(request.body)
        sos = SOSAlert.objects.get(id=data.get('sos_id'))
        sos.status = data.get('status')
        sos.save()
        return JsonResponse({'status': 'success', 'message': 'SOS status updated.'})
    except SOSAlert.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'SOS alert not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# API: DASHBOARD STATS
# ─────────────────────────────────────────
@login_required
@user_passes_test(is_admin)
def api_dashboard_stats(request):
    try:
        today = timezone.now().date()
        total_tourists = User.objects.filter(is_superuser=False).count()

        tourists_in_danger = 0
        for tourist in User.objects.filter(is_superuser=False):
            latest_sos = SOSAlert.objects.filter(tourist=tourist).order_by('-created_at').first()
            if latest_sos:
                lat, lon = float(latest_sos.latitude), float(latest_sos.longitude)
                for zone in DangerZone.objects.all():
                    if haversine_distance(lat, lon, zone.latitude, zone.longitude) * 1000 <= zone.radius:
                        tourists_in_danger += 1
                        break

        return JsonResponse({
            'status': 'success',
            'stats': {
                'total_tourists': total_tourists,
                'tourists_in_danger': tourists_in_danger,
                'total_sos_today': SOSAlert.objects.filter(created_at__date=today).count(),
                'total_danger_zones': DangerZone.objects.count(),
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def get_time_ago(dt):
    diff = timezone.now() - dt
    total_seconds = int(diff.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s ago"
    elif total_seconds < 3600:
        return f"{total_seconds // 60}m ago"
    elif total_seconds < 86400:
        return f"{total_seconds // 3600}h ago"
    else:
        return f"{diff.days}d ago"


def _has_active_session(user):
    """Check whether the user currently has any live Django session."""
    try:
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in active_sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(user.pk):
                return True
    except Exception:
        pass
    return False


def _clear_user_sessions(user):
    """Expire / delete all sessions belonging to a user."""
    try:
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in active_sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(user.pk):
                session.delete()
    except Exception:
        pass
