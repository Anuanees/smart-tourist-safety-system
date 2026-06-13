from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from core.models import Place, DangerZone


# ---------- HOMEPAGE ----------
def home(request):
    return render(request, 'accounts/index.html')


# ---------- PLACES ----------
def add_place(request):
    if request.method == 'POST':
        Place.objects.create(
            name=request.POST.get('name'),
            type=request.POST.get('type'),
            latitude=request.POST.get('latitude') or None,
            longitude=request.POST.get('longitude') or None,
            description=request.POST.get('description'),
        )
    return redirect('/accounts/admin-dashboard/#managePlaces')


def edit_place(request, place_id):
    place = get_object_or_404(Place, id=place_id)

    if request.method == "POST":
        place.name = request.POST.get("name")
        place.type = request.POST.get("type")
        place.latitude = request.POST.get("latitude") or None
        place.longitude = request.POST.get("longitude") or None
        place.description = request.POST.get("description")
        place.save()
        return redirect('/accounts/admin-dashboard/#managePlaces')

    return render(request, 'core/edit_place.html', {'place': place})


def delete_place(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    place.delete()
    return redirect('/accounts/admin-dashboard/#managePlaces')


# ---------- DANGER ZONES ----------
def add_zone(request):
    if request.method == 'POST':
        DangerZone.objects.create(
            name=request.POST.get('name'),
            risk_type=request.POST.get('risk_type'),
            severity=request.POST.get('severity'),
            latitude=request.POST.get('latitude') or None,
            longitude=request.POST.get('longitude') or None,
            additional_details=request.POST.get('additional_details'),
        )
    return redirect('/accounts/admin-dashboard/#manageZones')


def edit_zone(request, zone_id):
    zone = get_object_or_404(DangerZone, id=zone_id)

    if request.method == "POST":
        zone.name = request.POST.get("name")
        zone.risk_type = request.POST.get("risk_type")
        zone.severity = request.POST.get("severity")
        zone.latitude = request.POST.get("latitude") or None
        zone.longitude = request.POST.get("longitude") or None
        zone.additional_details = request.POST.get("additional_details")
        zone.save()
        return redirect('/accounts/admin-dashboard/#manageZones')

    return render(request, "core/edit_zone.html", {"zone": zone})


def delete_zone(request, zone_id):
    zone = get_object_or_404(DangerZone, id=zone_id)
    zone.delete()
    return redirect('/accounts/admin-dashboard/#manageZones')


# ---------- LOGOUT ----------
def user_logout(request):
    logout(request)
    return redirect('home')
