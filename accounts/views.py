# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from core.models import Place, DangerZone


# ---------------------------
# Public Home / Index
# ---------------------------
def index(request):
    return render(request, 'accounts/index.html')


# ---------------------------
# Tourist Views
# ---------------------------
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('tourist_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('tourist_dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'accounts/login.html')


def tourist_signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=full_name).exists():
            messages.error(request, 'Username already exists')
        else:
            User.objects.create_user(
                username=full_name,
                email=email,
                password=password
            )
            messages.success(request, 'Account created successfully')
            return redirect('login')

    return render(request, 'accounts/tourist_signup.html')


@never_cache
@login_required
def tourist_dashboard(request):
    response = render(request, 'accounts/tourist_dashboard.html')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# ---------------------------
# Admin Views
# ---------------------------
# admin_login removed – handled by unified login_view


@never_cache
@login_required
def admin_dashboard(request):
    from alerts.models import SOSAlert
    
    total_places = Place.objects.count()
    total_zones = DangerZone.objects.count()
    high_severity_zones = DangerZone.objects.filter(severity='High').count()
    total_sos = SOSAlert.objects.count()
    active_tourists = User.objects.filter(is_superuser=False).count()
    
    recent_places = Place.objects.all().order_by('-id')[:5]
    recent_zones = DangerZone.objects.all().order_by('-id')[:5]

    context = {
        'total_places': total_places,
        'total_zones': total_zones,
        'high_severity_zones': high_severity_zones,
        'total_sos': total_sos,
        'active_tourists': active_tourists,
        'recent_places': recent_places,
        'recent_zones': recent_zones,
    }

    response = render(request, 'accounts/admin_dashboard_new.html', context)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# ---------------------------
# MANAGE PLACES
# ---------------------------
@login_required
def manage_places(request):
    places = Place.objects.all().order_by('-id')
    context = {'places': places}
    return render(request, 'accounts/manage_places.html', context)


# ---------------------------
# MANAGE ZONES
# ---------------------------
@login_required
def manage_zones(request):
    zones = DangerZone.objects.all().order_by('-id')
    context = {'zones': zones}
    return render(request, 'accounts/manage_zones.html', context)


# ---------------------------
# MANAGE SOS
# ---------------------------
@login_required
def manage_sos(request):
    from alerts.models import SOSAlert
    sos_alerts = SOSAlert.objects.all().order_by('-created_at')
    context = {
        'sos_alerts': sos_alerts,
        'total_sos': sos_alerts.count()
    }
    return render(request, 'accounts/manage_sos.html', context)


# ---------------------------
# ADD PLACE
# ---------------------------
@login_required
def add_place(request):
    if request.method == "POST":
        Place.objects.create(
            name=request.POST.get('name'),
            type=request.POST.get('type'),
            latitude=request.POST.get('latitude'),
            longitude=request.POST.get('longitude'),
            description=request.POST.get('description')
        )
        messages.success(request, f"Place '{request.POST.get('name')}' added successfully!")
        return redirect('manage_places')
    return render(request, 'accounts/add_place.html')


# ---------------------------
# ADD DANGER ZONE
# ---------------------------
@login_required
def add_zone(request):
    if request.method == "POST":
        DangerZone.objects.create(
            name=request.POST.get('name'),
            risk_type=request.POST.get('risk_type'),
            severity=request.POST.get('severity'),
            latitude=request.POST.get('latitude'),
            longitude=request.POST.get('longitude'),
            radius=request.POST.get('radius', 500),
            additional_details=request.POST.get('additional_details')
        )
        messages.success(request, f"Danger zone '{request.POST.get('name')}' added successfully!")
        return redirect('manage_zones')
    return render(request, 'accounts/add_zone.html')


# ---------------------------
# DELETE PLACE
# ---------------------------
@login_required
def delete_place(request, id):
    place = get_object_or_404(Place, id=id)
    place_name = place.name
    place.delete()
    messages.success(request, f"Place '{place_name}' deleted successfully!")
    return redirect('manage_places')


# ---------------------------
# DELETE ZONE
# ---------------------------
@login_required
def delete_zone(request, id):
    zone = get_object_or_404(DangerZone, id=id)
    zone_name = zone.name
    zone.delete()
    messages.success(request, f"Danger zone '{zone_name}' deleted successfully!")
    return redirect('manage_zones')

# ---------------------------
# Change Password
# ---------------------------
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)   # keep user logged in
            return JsonResponse({'status': 'success', 'message': 'Password changed successfully!'})
        else:
            # Flatten errors into a single readable string
            error_list = []
            for field, errs in form.errors.items():
                for e in errs:
                    if field == '__all__':
                        error_list.append(str(e))
                    else:
                        error_list.append(str(e))
            return JsonResponse({'status': 'error', 'message': ' '.join(error_list)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)


# ---------------------------
# Logout
# ---------------------------
def logout_view(request):
    logout(request)
    request.session.flush()  # destroy session data completely
    response = redirect('index')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# ---------------------------
# BULK UPLOAD (CSV)
# ---------------------------
@login_required
def bulk_upload(request):
    if request.method == 'POST':
        import csv
        from io import TextIOWrapper
        from django.db import transaction
        
        upload_type = request.POST.get('upload_type')
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file to upload.')
            return render(request, 'accounts/bulk_upload.html')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File must be a CSV file (.csv extension).')
            return render(request, 'accounts/bulk_upload.html')
        
        try:
            # Read CSV file
            csv_file.seek(0)
            decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8')
            csv_reader = csv.DictReader(decoded_file)
            
            total_rows = 0
            success_count = 0
            skipped_count = 0
            error_messages = []
            
            if upload_type == 'danger_zones':
                # Validate headers
                required_headers = ['name', 'latitude', 'longitude', 'severity', 'radius', 'description']
                if not all(header in csv_reader.fieldnames for header in required_headers):
                    messages.error(request, f'Invalid CSV headers. Required: {", ".join(required_headers)}')
                    return render(request, 'accounts/bulk_upload.html')
                
                with transaction.atomic():
                    for row_num, row in enumerate(csv_reader, start=2):
                        total_rows += 1
                        
                        # Skip empty rows
                        if not row.get('name') or not row.get('name').strip():
                            skipped_count += 1
                            error_messages.append(f'Row {row_num}: Empty name, skipped')
                            continue
                        
                        try:
                            # Validate severity
                            severity = row['severity'].strip()
                            if severity not in ['Low', 'Medium', 'High']:
                                skipped_count += 1
                                error_messages.append(f'Row {row_num}: Invalid severity "{severity}". Must be Low, Medium, or High')
                                continue
                            
                            # Validate coordinates
                            try:
                                lat = float(row['latitude'])
                                lon = float(row['longitude'])
                            except (ValueError, TypeError):
                                skipped_count += 1
                                error_messages.append(f'Row {row_num}: Invalid latitude/longitude values')
                                continue
                            
                            # Validate radius
                            try:
                                radius = int(row['radius'])
                                if radius <= 0:
                                    raise ValueError
                            except (ValueError, TypeError):
                                skipped_count += 1
                                error_messages.append(f'Row {row_num}: Invalid radius. Must be a positive number')
                                continue
                            
                            # Check for duplicates
                            name = row['name'].strip()
                            if DangerZone.objects.filter(name=name, latitude=lat, longitude=lon).exists():
                                skipped_count += 1
                                error_messages.append(f'Row {row_num}: Duplicate zone "{name}" at same coordinates')
                                continue
                            
                            # Create danger zone
                            DangerZone.objects.create(
                                name=name,
                                latitude=lat,
                                longitude=lon,
                                severity=severity,
                                radius=radius,
                                risk_type=row.get('risk_type', 'Other').strip(),
                                additional_details=row.get('description', '').strip()
                            )
                            success_count += 1
                            
                        except Exception as e:
                            skipped_count += 1
                            error_messages.append(f'Row {row_num}: Error - {str(e)}')
            
            elif upload_type == 'places':
                # Validate headers
                required_headers = ['name', 'type', 'latitude', 'longitude', 'description']
                if not all(header in csv_reader.fieldnames for header in required_headers):
                    messages.error(request, f'Invalid CSV headers. Required: {", ".join(required_headers)}')
                    return render(request, 'accounts/bulk_upload.html')
                
                with transaction.atomic():
                    for row_num, row in enumerate(csv_reader, start=2):
                        total_rows += 1
                        
                        # Skip empty rows
                        if not row.get('name') or not row.get('name').strip():
                            skipped_count += 1
                            error_messages.append(f'Row {row_num}: Empty name, skipped')
                            continue
                        
                        try:
                            # Validate type
                            place_type = row['type'].strip()
                            if place_type not in ['Police Station', 'Hospital', 'Help Center']:
                                skipped_count += 1
                                error_messages.append(f'Row {row_num}: Invalid type "{place_type}". Must be Police Station, Hospital, or Help Center')
                                continue
                            
                            # Validate coordinates
                            try:
                                lat = float(row['latitude'])
                                lon = float(row['longitude'])
                            except (ValueError, TypeError):
                                skipped_count += 1
                                error_messages.append(f'Row {row_num}: Invalid latitude/longitude values')
                                continue
                            
                            # Check for duplicates
                            name = row['name'].strip()
                            if Place.objects.filter(name=name, latitude=lat, longitude=lon).exists():
                                skipped_count += 1
                                error_messages.append(f'Row {row_num}: Duplicate place "{name}" at same coordinates')
                                continue
                            
                            # Create place
                            Place.objects.create(
                                name=name,
                                type=place_type,
                                latitude=lat,
                                longitude=lon,
                                description=row.get('description', '').strip()
                            )
                            success_count += 1
                            
                        except Exception as e:
                            skipped_count += 1
                            error_messages.append(f'Row {row_num}: Error - {str(e)}')
            
            else:
                messages.error(request, 'Please select a valid upload type.')
                return render(request, 'accounts/bulk_upload.html')
            
            # Show results
            if success_count > 0:
                messages.success(request, f'✓ Successfully uploaded {success_count} of {total_rows} records!')
            
            if skipped_count > 0:
                error_summary = f'⚠ Skipped {skipped_count} rows. '
                if len(error_messages) <= 10:
                    error_summary += '<br>' + '<br>'.join(error_messages)
                else:
                    error_summary += '<br>' + '<br>'.join(error_messages[:10])
                    error_summary += f'<br>... and {len(error_messages) - 10} more errors'
                messages.warning(request, error_summary)
            
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
    
    return render(request, 'accounts/bulk_upload.html')
