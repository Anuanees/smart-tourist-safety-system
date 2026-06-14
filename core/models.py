from django.db import models

# Existing Place model
class Place(models.Model):
    PLACE_TYPES = [
        ('Hospital', 'Hospital'),
        ('Police Station', 'Police Station'),
        ('Help Center', 'Help Center'),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=PLACE_TYPES)
    address = models.CharField(max_length=255, blank=True)  # optional text address
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# New DangerZone model
class DangerZone(models.Model):
    RISK_TYPES = [
        ('Crime', 'Crime'),
        ('Flood', 'Flood'),
        ('Landslide', 'Landslide'),
    ]
    SEVERITY = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    name = models.CharField(max_length=100)
    risk_type = models.CharField(max_length=50, choices=RISK_TYPES)
    severity = models.CharField(max_length=50, choices=SEVERITY)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    additional_details = models.TextField(blank=True)
    radius = models.IntegerField(default=500, help_text='Geofence radius in meters')

    def __str__(self):
        return self.name

# ─────────────────────────────────────────────────────────
# TouristLocation — stores periodic GPS pings from the Flutter app.
# New model added for Phase 1 location tracking feature.
# Does NOT affect Place or DangerZone.
# ─────────────────────────────────────────────────────────
class TouristLocation(models.Model):
    tourist   = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='locations',
    )
    latitude  = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'

    def __str__(self):
        return "{} @ {} ({}, {})".format(
            self.tourist.username,
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.latitude,
            self.longitude,
        )
