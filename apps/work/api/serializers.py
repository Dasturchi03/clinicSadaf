from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.category.api.nested_serializers import NestedPrintOutCategorySerializer
from apps.category.models import Category, PrintOutCategory
from apps.core.api.fields import SerializedPKRelatedField
from apps.disease.models import Disease
from apps.specialization.models import Specialization
from apps.work.models import Work


class WorkCategorySerializer(serializers.ModelSerializer):
    # Категории при создании работ

    category_id = serializers.IntegerField(required=False)

    class Meta:
        model = Category
        fields = ["category_id", "category_title"]
        extra_kwargs = {
            "category_id": {"read_only": True},
            "category_title": {"read_only": True},
        }


class WorkDiseaseSerializer(serializers.ModelSerializer):
    # Болезни при создании работ

    disease_id = serializers.IntegerField(required=False)

    class Meta:
        model = Disease
        fields = ["disease_id", "disease_title"]
        extra_kwargs = {
            "disease_id": {"read_only": True},
            "disease_title": {"read_only": True},
        }


class WorkSpecializationSerializer(serializers.ModelSerializer):
    # Специализации при создании работ

    specialization_id = serializers.IntegerField(required=False)

    class Meta:
        model = Specialization
        fields = ["specialization_id", "specialization_text"]
        extra_kwargs = {
            "specialization_id": {"read_only": True},
            "specialization_text": {"read_only": True},
        }


class WorkSerializer(serializers.ModelSerializer):
    # Работа
    category = WorkCategorySerializer(many=True, required=False)
    disease = WorkDiseaseSerializer(many=True, required=False)
    specialization = WorkSpecializationSerializer(many=True, required=False)
    print_out_categories = SerializedPKRelatedField(
        queryset=PrintOutCategory.objects.only("id"),
        serializer=NestedPrintOutCategorySerializer,
        many=True,
        required=False,
    )

    class Meta:
        model = Work
        fields = [
            "work_id",
            "work_type",
            "work_salary_type",
            "category",
            "disease",
            "specialization",
            "print_out_categories",
            "work_title",
            "work_title_ru",
            "work_title_en",
            "work_title_uz",
            "work_basic_price",
            "work_vip_price",
            "work_discount_price",
            "work_discount_percent",
            "work_fixed_salary_amount",
            "work_hybrid_salary_amount",
        ]
        extra_kwargs = {
            "work_id": {"read_only": True},
            "work_title": {"read_only": True},
            "work_vip_price": {"required": False},
            "work_discount_price": {"required": False},
            "work_discount_percent": {"required": False},
            "work_fixed_salary_amount": {"required": False},
            "work_hybrid_salary_amount": {"required": False},
        }

    def to_representation(self, instance):
        data = super(WorkSerializer, self).to_representation(instance)
        current_user = self.context.get("current_user")
        private_fields = [
            "work_basic_price",
            "work_vip_price",
            "work_discount_percent",
            "work_discount_price",
            "work_fixed_salary_amount",
            "work_hybrid_salary_amount",
        ]

        for field, field_value in sorted(data.items()):
            if field in private_fields:
                if not current_user.has_perm("work.view_work_private_info"):
                    data.pop(field)
        return data

    def to_internal_value(self, data):
        if self.context.get("action") == "partial_update":
            current_user = self.context.get("current_user")
            private_fields = [
                "work_basic_price",
                "work_vip_price",
                "work_discount_percent",
                "work_discount_price",
                "work_fixed_salary_amount",
                "work_hybrid_salary_amount",
            ]
            errors = {}

            for field, field_value in sorted(data.items()):

                if field in private_fields:
                    if not current_user.has_perm("work.change_work_private_info"):
                        errors[field] = ["This field is not allowed to change"]
            if errors:
                raise ValidationError(errors)
            return data
        else:
            return super(WorkSerializer, self).to_representation(data)

    def create(self, validated_data):
        category_data = validated_data.pop("category", None)
        disease_data = validated_data.pop("disease", None)
        specialization_data = validated_data.pop("specialization", None)

        instance = super().create(validated_data)

        # Добавление категорий относящихся к этой категории
        if category_data:
            category_list = Category.objects.filter(
                pk__in=[category_id["category_id"] for category_id in category_data]
            )
            instance.category.add(*category_list)

        if disease_data:
            disease_list = Disease.objects.filter(
                pk__in=[disease_id["disease_id"] for disease_id in disease_data]
            )
            instance.disease.add(*disease_list)

        # Добавление специализаций относящихся к этой категории
        if specialization_data:
            specialization_list = Specialization.objects.filter(
                pk__in=[
                    specialization_id["specialization_id"]
                    for specialization_id in specialization_data
                ]
            )
            instance.specialization.add(*specialization_list)
        return instance

    def update(self, instance, validated_data):
        category_data = validated_data.pop("category", None)
        disease_data = validated_data.pop("disease", None)
        specialization_data = validated_data.pop("specialization", None)

        instance = super().update(instance, validated_data)

        # Добавление категорий относящихся к этой категории
        if category_data:
            instance.category.clear()
            category_list = Category.objects.filter(
                pk__in=[category_id["category_id"] for category_id in category_data]
            )
            instance.category.add(*category_list)

        # Добавление болезней относящихся к этой категории
        if disease_data:
            instance.disease.clear()
            disease_list = Disease.objects.filter(
                pk__in=[disease_id["disease_id"] for disease_id in disease_data]
            )
            instance.disease.add(*disease_list)

        # Добавление специализаций относящихся к этой категории
        if specialization_data:
            instance.specialization.clear()
            specialization_list = Specialization.objects.filter(
                pk__in=[
                    specialization_id["specialization_id"]
                    for specialization_id in specialization_data
                ]
            )
            instance.specialization.add(*specialization_list)
        return instance


class WorkDetailSerializer(serializers.ModelSerializer):
    # Работы при создании специализации, категории, болезни

    work_id = serializers.IntegerField(required=False)

    class Meta:
        model = Work
        fields = [
            "work_id",
            "work_type",
            "work_salary_type",
            "work_title",
            "work_basic_price",
            "work_vip_price",
            "work_discount_price",
            "work_discount_percent",
            "work_fixed_salary_amount",
            "work_hybrid_salary_amount",
        ]
        extra_kwargs = {
            "work_type": {"read_only": True},
            "work_salary_type": {"read_only": True},
            "work_title": {"read_only": True},
            "work_basic_price": {"read_only": True},
            "work_vip_price": {"read_only": True},
            "work_discount_price": {"read_only": True},
            "work_discount_percent": {"read_only": True},
            "work_fixed_salary_amount": {"read_only": True},
            "work_hybrid_salary_amount": {"read_only": True},
        }
