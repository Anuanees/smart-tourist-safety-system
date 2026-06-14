# api/serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers
from core.models import Place, DangerZone, TouristLocation
from alerts.models import SOSAlert


# ─────────────────────────────────────────
# USER SERIALIZER
# ─────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

    def get_role(self, obj):
        return 'admin' if obj.is_superuser else 'tourist'


# ─────────────────────────────────────────
# PLACE SERIALIZER
# ─────────────────────────────────────────
class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name', 'type', 'latitude', 'longitude', 'description', 'address']


# ─────────────────────────────────────────
# DANGER ZONE SERIALIZER
# ─────────────────────────────────────────
class DangerZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DangerZone
        fields = [
            'id', 'name', 'risk_type', 'severity',
            'latitude', 'longitude', 'additional_details', 'radius'
        ]


# ─────────────────────────────────────────
# SOS ALERT SERIALIZER
# ─────────────────────────────────────────
class SOSAlertSerializer(serializers.ModelSerializer):
    tourist_username = serializers.CharField(source='tourist.username', read_only=True)

    class Meta:
        model = SOSAlert
        fields = [
            'id', 'tourist', 'tourist_username',
            'latitude', 'longitude',
            'nearest_help_center', 'distance_km',
            'status', 'created_at'
        ]
        read_only_fields = ['tourist', 'nearest_help_center', 'distance_km', 'status', 'created_at']


# ─────────────────────────────────────────
# CHANGE PASSWORD SERIALIZER
# ─────────────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


# ─────────────────────────────────────────
# TOURIST REGISTRATION SERIALIZER
# ─────────────────────────────────────────
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=150)
    email    = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_staff=False,
            is_superuser=False,
        )

# ─────────────────────────────────────────────────────────
# TOURIST LOCATION SERIALIZER
# Added for Phase 1 — location tracking.
# Does NOT affect any existing serializer.
# ─────────────────────────────────────────────────────────
class TouristLocationSerializer(serializers.ModelSerializer):
    tourist_username = serializers.CharField(source='tourist.username', read_only=True)

    class Meta:
        model  = TouristLocation
        fields = ['id', 'tourist', 'tourist_username', 'latitude', 'longitude', 'timestamp']
        read_only_fields = ['tourist', 'timestamp']
