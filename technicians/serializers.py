from rest_framework import serializers
from .models import Technician, TechnicianAssistant, TechnicianService, TechnicianRecommendation


class TechnicianAssistantSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianAssistant
        fields = ['id', 'name', 'phone_number', 'email', 'role', 'is_active']


class TechnicianServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianService
        fields = ['id', 'service_name', 'description', 'typical_cost', 'estimated_duration', 'is_active']


class TechnicianSerializer(serializers.ModelSerializer):
    assistants = TechnicianAssistantSerializer(many=True, read_only=True)
    services = TechnicianServiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Technician
        fields = [
            'id', 'company_name', 'technician_name', 'email', 'phone_number',
            'alternate_phone', 'address', 'specialization', 'is_active',
            'assistants', 'services', 'created_at', 'updated_at'
        ]


class TechnicianRecommendationSerializer(serializers.ModelSerializer):
    technician_name = serializers.CharField(source='technician.technician_name', read_only=True)
    company_name = serializers.CharField(source='technician.company_name', read_only=True)
    asset_id = serializers.CharField(source='asset.asset_id', read_only=True)
    
    class Meta:
        model = TechnicianRecommendation
        fields = [
            'id', 'technician', 'technician_name', 'company_name',
            'asset', 'asset_id', 'recommendation_type', 'description',
            'estimated_cost', 'priority', 'is_completed', 'completed_date',
            'notes', 'created_at'
        ]
