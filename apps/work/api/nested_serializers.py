from rest_framework import serializers

from apps.work.models import Work


class NestedWorkPrintOutCategorySerializer(serializers.ModelSerializer):
    # used in endpoints for print out categories
    class Meta:
        model = Work
        fields = ["work_id", "work_title"]


class NestedWorkReservationSerializer(serializers.ModelSerializer):
    # used in endpoints for reservation
    class Meta:
        model = Work
        fields = ("work_id", "work_title", "work_basic_price", "estimated_duration_days")
