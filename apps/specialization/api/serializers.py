from rest_framework import serializers

from apps.specialization.models import Specialization
from apps.work.models import Work
from apps.work.api.serializers import WorkDetailSerializer
from apps.user.models import User


class SpecializationDoctorSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'user_type',
            'user_firstname',
            'user_lastname'
        ]


class SpecializationSerializer(serializers.ModelSerializer):
    # Создание специализаций
    work_specialization = WorkDetailSerializer(many=True, required=False)
    user_specialization = SpecializationDoctorSerializer(many=True, read_only=True)

    class Meta:
        model = Specialization
        fields = [
            "specialization_id",
            "specialization_text",
            "specialization_text_ru",
            "specialization_text_en",
            "specialization_text_uz",
            "work_specialization",
            "user_specialization"
        ]
        extra_kwargs = {
            "specialization_id": {"read_only": True},
            "specialization_text": {"read_only": True}
        }

    def create(self, validated_data):
        specialization = Specialization.objects.create(specialization_text_ru=validated_data['specialization_text_ru'],
                                                       specialization_text_en=validated_data['specialization_text_en'],
                                                       specialization_text_uz=validated_data['specialization_text_uz'])

        # Добавление специализации к выбранным работам
        work_specialization_data = validated_data.pop('work_specialization', None)
        if work_specialization_data:
            work_list = Work.objects.filter(work_id__in=[work_id['work_id'] for work_id in work_specialization_data])
            for work in work_list:
                work.specialization.add(specialization)
        return specialization

    def update(self, instance, validated_data):
        instance.specialization_text_ru = validated_data.get('specialization_text_ru', instance.specialization_text_ru)
        instance.specialization_text_en = validated_data.get('specialization_text_en', instance.specialization_text_en)
        instance.specialization_text_uz = validated_data.get('specialization_text_uz', instance.specialization_text_uz)

        # Добавление специализации к выбранным работам
        work_specialization_data = validated_data.pop('work_specialization', None)
        if work_specialization_data:
            instance.work_specialization.clear()
            work_list = Work.objects.filter(work_id__in=[work_id['work_id'] for work_id in work_specialization_data])
            for work in work_list:
                work.specialization.add(instance)
        instance.save()
        return instance

