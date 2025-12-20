from rest_framework import serializers

from apps.category.models import Category, PrintOutCategory
from apps.core.api.fields import SerializedPKRelatedField
from apps.core.api.mixins import AutoUniqueValidatorMixin
from apps.work.api.nested_serializers import NestedWorkPrintOutCategorySerializer
from apps.work.api.serializers import WorkDetailSerializer
from apps.work.models import Work


class PrintOutCategorySerializer(AutoUniqueValidatorMixin, serializers.ModelSerializer):
    works = SerializedPKRelatedField(
        queryset=Work.objects.only("work_id", "work_title"),
        serializer=NestedWorkPrintOutCategorySerializer,
        many=True,
        required=False,
    )

    class Meta:
        model = PrintOutCategory
        fields = ["id", "name", "name_ru", "name_en", "name_uz", "order_index", "works"]
        extra_kwargs = {
            "name": {"read_only": True},
            "name_ru": {"write_only": True},
            "name_en": {"write_only": True},
            "name_uz": {"write_only": True},
        }


class PrintOutCategoryDetailSerializer(
    AutoUniqueValidatorMixin, serializers.ModelSerializer
):
    works = SerializedPKRelatedField(
        queryset=Work.objects.only("work_id", "work_title"),
        serializer=NestedWorkPrintOutCategorySerializer,
        many=True,
        required=False,
    )

    class Meta:
        model = PrintOutCategory
        fields = ["id", "name", "name_ru", "name_en", "name_uz", "order_index", "works"]
        extra_kwargs = {
            "name": {"read_only": True},
        }


class CategorySerializer(serializers.ModelSerializer):
    # Создание категории
    work_category = WorkDetailSerializer(many=True, required=False)

    class Meta:
        model = Category
        fields = [
            "category_id",
            "category_title",
            "category_title_ru",
            "category_title_en",
            "category_title_uz",
            "work_category",
        ]
        extra_kwargs = {"category_title": {"read_only": True}}

    def create(self, validated_data):
        category = Category.objects.create(
            category_title_ru=validated_data["category_title_ru"],
            category_title_en=validated_data["category_title_en"],
            category_title_uz=validated_data["category_title_uz"],
        )

        work_category_data = validated_data.pop("work_category", None)
        if work_category_data:
            work_list = Work.objects.filter(
                work_id__in=[work_id["work_id"] for work_id in work_category_data]
            )
            for work in work_list:
                work.category.add(category)

        return category

    def update(self, instance, validated_data):
        instance.category_title_ru = validated_data.get(
            "category_title_ru", instance.category_title_ru
        )
        instance.category_title_en = validated_data.get(
            "category_title_en", instance.category_title_en
        )
        instance.category_title_uz = validated_data.get(
            "category_title_uz", instance.category_title_uz
        )

        # Обновление работ относящихся к этой категории
        work_category_data = validated_data.pop("work_category", None)
        if work_category_data:
            instance.work_category.clear()
            work_list = Work.objects.filter(
                work_id__in=[work_id["work_id"] for work_id in work_category_data]
            )
            for work in work_list:
                work.category.add(instance)
        instance.save()
        return instance
