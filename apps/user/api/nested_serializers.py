from rest_framework import serializers

from apps.user.models import User


class NestedDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "user_firstname", "user_lastname"]
