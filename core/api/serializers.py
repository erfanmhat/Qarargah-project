from rest_framework import serializers
from core.models import (
    Soldier, Leave, ServiceStatus, HealthStatus, ServiceLocation,
    ServiceReductionType, SoldierServiceReduction
)


class SoldierServiceReductionSerializer(serializers.ModelSerializer):
    reduction_type_title = serializers.CharField(source='reduction_type.title', read_only=True)
    
    class Meta:
        model = SoldierServiceReduction
        fields = ['id', 'reduction_type', 'reduction_type_title', 'days', 'created_at']


class SoldierSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    service_status_title = serializers.CharField(source='service_status.title', read_only=True, allow_null=True)
    health_status_title = serializers.CharField(source='health_status.title', read_only=True, allow_null=True)
    current_location_name = serializers.CharField(source='current_location.name', read_only=True, allow_null=True)
    service_end_date = serializers.SerializerMethodField()
    total_reduction_days = serializers.SerializerMethodField()
    reductions = SoldierServiceReductionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Soldier
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'national_code', 'dossier_code',
            'dispatch_type', 'service_start_date', 'arrival_date', 'birth_date',
            'service_status', 'service_status_title', 'health_status', 'health_status_title',
            'current_location', 'current_location_name',             'phone_personal', 'phone_parent',
            'phone_home', 'phone_work', 'home_address', 'guard_code',
            'service_end_date', 'total_reduction_days', 'reductions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_service_end_date(self, obj):
        end_date = obj.service_end_date()
        return end_date.isoformat() if end_date else None
    
    def get_total_reduction_days(self, obj):
        return obj.total_reduction_days()


class LeaveSerializer(serializers.ModelSerializer):
    soldier_name = serializers.CharField(source='soldier.full_name', read_only=True)
    soldier_national_code = serializers.CharField(source='soldier.national_code', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    
    class Meta:
        model = Leave
        fields = [
            'id', 'soldier', 'soldier_name', 'soldier_national_code', 'leave_type',
            'leave_type_display', 'start_date', 'end_date', 'days', 'is_approved',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['days', 'created_at', 'updated_at']


class ServiceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStatus
        fields = ['id', 'title', 'is_active_service']


class HealthStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthStatus
        fields = ['id', 'title', 'is_exempt_from_combat']


class ServiceLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceLocation
        fields = ['id', 'name', 'parent']


class DashboardStatsSerializer(serializers.Serializer):
    total_soldiers = serializers.IntegerField()
    on_leave_today = serializers.IntegerField()
    ending_soon = serializers.IntegerField()

