import os

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.vacancies.models import (
    Vacancy,
    VacancyApplication,
    VacancyApplicationStatus,
)


ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_RESUME_FILE_SIZE = 10 * 1024 * 1024


class VacancySerializer(serializers.ModelSerializer):
    applications_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            "vacancy_id",
            "title",
            "title_ru",
            "title_en",
            "title_uz",
            "description",
            "description_ru",
            "description_en",
            "description_uz",
            "requirements",
            "requirements_ru",
            "requirements_en",
            "requirements_uz",
            "responsibilities",
            "responsibilities_ru",
            "responsibilities_en",
            "responsibilities_uz",
            "conditions",
            "conditions_ru",
            "conditions_en",
            "conditions_uz",
            "salary_from",
            "salary_to",
            "address",
            "phone",
            "email",
            "deadline",
            "is_active",
            "sort_order",
            "applications_count",
            "updated_at",
            "created_at",
        ]
        extra_kwargs = {
            "vacancy_id": {"read_only": True},
            "title": {"read_only": True},
            "description": {"read_only": True},
            "requirements": {"read_only": True},
            "responsibilities": {"read_only": True},
            "conditions": {"read_only": True},
        }


class VacancyPublicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = [
            "vacancy_id",
            "title",
            "description",
            "salary_from",
            "salary_to",
            "address",
            "phone",
            "email",
            "deadline",
            "is_active",
            "sort_order",
        ]


class VacancyPublicDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = [
            "vacancy_id",
            "title",
            "description",
            "requirements",
            "responsibilities",
            "conditions",
            "salary_from",
            "salary_to",
            "address",
            "phone",
            "email",
            "deadline",
            "is_active",
            "sort_order",
            "updated_at",
            "created_at",
        ]


class VacancyApplicationSerializer(serializers.ModelSerializer):
    vacancy_title = serializers.CharField(source="vacancy.title", read_only=True)
    resume_file_url = serializers.SerializerMethodField()

    class Meta:
        model = VacancyApplication
        fields = [
            "application_id",
            "vacancy",
            "vacancy_title",
            "first_name",
            "last_name",
            "middle_name",
            "phone",
            "email",
            "address",
            "birth_date",
            "gender",
            "marital_status",
            "message",
            "resume_file",
            "resume_file_url",
            "status",
            "updated_at",
            "created_at",
        ]
        extra_kwargs = {
            "application_id": {"read_only": True},
            "status": {"read_only": True},
        }

    def get_resume_file_url(self, obj):
        request = self.context.get("request")
        if obj.resume_file and hasattr(obj.resume_file, "url"):
            if request:
                return request.build_absolute_uri(obj.resume_file.url)
            return obj.resume_file.url
        return None

    def validate_resume_file(self, value):
        if not value:
            raise serializers.ValidationError(_("Resume file is required."))

        ext = os.path.splitext(value.name)[1].replace(".", "").lower()
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            raise serializers.ValidationError(
                _("Allowed file formats: pdf, doc, docx.")
            )

        if value.size > MAX_RESUME_FILE_SIZE:
            raise serializers.ValidationError(
                _("Resume file size must not exceed 10 MB.")
            )
        return value

    def validate(self, attrs):
        vacancy = attrs.get("vacancy")
        if vacancy and not vacancy.is_active:
            raise serializers.ValidationError(
                {"vacancy": _("You cannot apply to an inactive vacancy.")}
            )
        return attrs

    def create(self, validated_data):
        return VacancyApplication.objects.create(**validated_data)


class VacancyApplicationAdminSerializer(serializers.ModelSerializer):
    vacancy_title = serializers.CharField(source="vacancy.title", read_only=True)
    resume_file_url = serializers.SerializerMethodField()

    class Meta:
        model = VacancyApplication
        fields = [
            "application_id",
            "vacancy",
            "vacancy_title",
            "first_name",
            "last_name",
            "middle_name",
            "phone",
            "email",
            "address",
            "birth_date",
            "gender",
            "marital_status",
            "message",
            "resume_file",
            "resume_file_url",
            "status",
            "updated_at",
            "created_at",
        ]

    def get_resume_file_url(self, obj):
        request = self.context.get("request")
        if obj.resume_file and hasattr(obj.resume_file, "url"):
            if request:
                return request.build_absolute_uri(obj.resume_file.url)
            return obj.resume_file.url
        return None


class VacancyApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyApplication
        fields = ["status"]

    def validate_status(self, value):
        allowed = {choice[0] for choice in VacancyApplicationStatus.choices}
        if value not in allowed:
            raise serializers.ValidationError(_("Invalid status."))
        return value
