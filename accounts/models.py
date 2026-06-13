from django.db import models

# Tourist model (already exists)
class Tourist(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username

# Tourist places (Hospitals, Police Stations, Help Centers)
class Place(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Danger zones
class DangerZone(models.Model):
    RISK_CHOICES = [
        ('Crime', 'Crime'),
        ('Flood', 'Flood'),
        ('Landslide', 'Landslide'),
    ]
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    name = models.CharField(max_length=100)
    risk_type = models.CharField(max_length=50, choices=RISK_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    additional_details = models.TextField(blank=True)

    def __str__(self):
        return self.name
