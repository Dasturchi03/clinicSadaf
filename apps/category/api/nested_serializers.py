from rest_framework import serializers

from apps.category.models import PrintOutCategory


class NestedPrintOutCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintOutCategory
        fields = ["id", "name"]
