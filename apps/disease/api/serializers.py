from rest_framework import serializers

from apps.disease.models import Disease

from apps.work.models import Work
from apps.work.api.serializers import WorkDetailSerializer


class DiseaseSerializer(serializers.ModelSerializer):
    # Создание болезни
    work_disease = WorkDetailSerializer(many=True, required=False)
    parent = serializers.PrimaryKeyRelatedField(queryset=Disease.objects.all(), required=False, allow_null=True)
    disease_child = serializers.SerializerMethodField("get_disease_child")

    class Meta:
        model = Disease
        fields = [
            "disease_id",
            "parent",
            "disease_title",
            "disease_title_ru",
            "disease_title_en",
            "disease_title_uz",
            "disease_child",
            "work_disease"
        ]
        extra_kwargs = {
            "disease_id": {"read_only": True},
            "disease_title": {"read_only": True},
        }

    def get_disease_child(self, obj):
        queryset = Disease.objects.filter(parent=obj)
        serializer = DiseaseSerializer(queryset, many=True)
        return serializer.data

    def create(self, validated_data):
        disease = Disease(parent=validated_data.get("parent", None),
                          disease_title_ru=validated_data["disease_title_ru"],
                          disease_title_en=validated_data["disease_title_en"],
                          disease_title_uz=validated_data["disease_title_uz"])
        disease.save()

        work_disease_data = validated_data.pop("work_disease", None)
        if work_disease_data:
            work_list = Work.objects.filter(work_id__in=[work_id["work_id"] for work_id in work_disease_data])
            for work in work_list:
                work.disease.add(disease)
        return disease

    def update(self, instance, validated_data):
        instance.disease_title_ru = validated_data.get("disease_title_ru", instance.disease_title_ru)
        instance.disease_title_en = validated_data.get("disease_title_en", instance.disease_title_en)
        instance.disease_title_uz = validated_data.get("disease_title_uz", instance.disease_title_uz)
        instance.parent = validated_data.get("parent", instance.parent)

        work_disease_data = validated_data.pop("work_disease", None)
        if work_disease_data:
            instance.work_disease.clear()
            work_list = Work.objects.filter(work_id__in=[work_id["work_id"] for work_id in work_disease_data])
            for work in work_list:
                work.disease.add(instance)
        instance.save()
        return instance


class DiseaseListSerializer(serializers.ModelSerializer):
    # Болезнь
    work_disease = WorkDetailSerializer(many=True, required=False)
    disease_child = DiseaseSerializer(many=True, required=False)

    class Meta:
        model = Disease
        fields = [
            "disease_id",
            "parent",
            "disease_child",
            "disease_title",
            "work_disease"
        ]
        extra_kwargs = {
            "disease_id": {"read_only": True},
            "disease_title": {"read_only": True}
        }
