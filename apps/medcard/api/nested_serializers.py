from rest_framework import serializers

from apps.medcard.models import Tooth


class NestedToothSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tooth
        fields = ["tooth_id", "tooth_type", "tooth_number", "tooth_image"]
