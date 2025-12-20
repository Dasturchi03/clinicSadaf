from datetime import datetime, time, timedelta

from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.specialization.models import Specialization
from apps.user.api.nested_serializers import NestedDoctorSerializer
from apps.user.models import (
    User,
    User_Private_Phone,
    User_Public_Phone,
    User_Type,
    UserSalary,
    UserSchedule,
)
from apps.work.api.serializers import WorkSerializer


class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super(TokenObtainPairSerializer, self).validate(attrs)
        refresh = self.get_token(self.user)
        new_token = refresh.access_token
        token_exp_time = (
            datetime.combine(datetime.today(), time(23, 59)) - timezone.now()
        ).seconds / 60
        new_token.set_exp(lifetime=timedelta(minutes=token_exp_time))
        data["refresh"] = str(refresh)
        data["access"] = str(new_token)

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["username"] = user.username
        token["user_id"] = user.id
        token["user_fullname"] = "{} {}".format(user.user_firstname, user.user_lastname)
        token["user_image"] = str(user.user_image)

        return token


class ChoiceField(serializers.ChoiceField):

    def to_representation(self, obj):
        if obj == "" and self.allow_blank:
            return obj
        return self._choices[obj]

    def to_internal_value(self, data):
        # To support inserts with the value
        if data == "" and self.allow_blank:
            return ""

        for key, val in self._choices.items():
            if val == data:
                return key
        self.fail("invalid_choice", input=data)


class DoctorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = User
        fields = ["id", "user_firstname", "user_lastname"]
        extra_kwargs = {
            "user_firstname": {"read_only": True},
            "user_lastname": {"read_only": True},
        }


class PermissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]
        extra_kwargs = {"name": {"read_only": True}, "codename": {"read_only": True}}


class GroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ["id", "name", "permissions"]
        extra_kwargs = {"name": {"read_only": True}}


class UserPermissionsSerializer(serializers.ModelSerializer):
    # id, email, groups, user_permissions
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "is_superuser", "permissions"]

    def get_permissions(self, obj):
        user = self.context.get("user")
        result = []
        groups = user.groups.filter(user=user)
        for index in groups:
            result.append(index.name)
        query = Permission.objects.filter(
            Q(group__name__in=result) | Q(user=user)
        ).distinct()
        serializer = PermissionSerializer(query, many=True)
        return serializer.data


class UserPrivatePhoneSerializer(serializers.ModelSerializer):
    # Фильтр не удаленных приватных контактов админа
    user_phone_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = User_Private_Phone
        fields = ["user_phone_id", "private_phone"]


class UserPublicPhoneSerializer(serializers.ModelSerializer):
    # Фильтр не удаленных публичных контактов админа
    user_phone_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = User_Public_Phone
        fields = ["user_phone_id", "public_phone"]


class UserSpecializationSerializer(serializers.ModelSerializer):
    # Специализации доктора
    specialization_id = serializers.IntegerField(required=False)

    class Meta:
        model = Specialization
        fields = ["specialization_id", "specialization_text"]
        extra_kwargs = {"specialization_text": {"read_only": True}}


class UserTypeInsertSerializer(serializers.ModelSerializer):
    user_type_id = serializers.IntegerField(required=False)

    class Meta:
        model = User_Type
        fields = ["user_type_id", "type_text"]
        extra_kwargs = {"type_text": {"read_only": True}}


class ScheduleSerializer(serializers.ModelSerializer):
    schedule_id = serializers.IntegerField(required=False)
    work_start_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )
    work_end_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )
    lunch_start_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )
    lunch_end_time = serializers.TimeField(
        format="%H:%M", input_formats=["%H:%M"], required=False
    )
    is_working = serializers.BooleanField(default=True, required=False)
    one_time_update = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = UserSchedule
        fields = [
            "schedule_id",
            "user",
            "day",
            "work_start_time",
            "work_end_time",
            "lunch_start_time",
            "lunch_end_time",
            "is_working",
            "one_time_update",
        ]
        extra_kwargs = {"day": {"required": False}, "user": {"read_only": True}}


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=50, min_length=8, write_only=True)
    password2 = serializers.CharField(max_length=50, min_length=8, write_only=True)
    user_public_phone = UserPublicPhoneSerializer(many=True, required=False)
    user_private_phone = UserPrivatePhoneSerializer(many=True)
    user_specialization = UserSpecializationSerializer(many=True, required=False)
    user_birthdate = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )
    user_schedule = ScheduleSerializer(many=True, required=False)
    user_type = UserTypeInsertSerializer()
    groups = GroupSerializer(many=True)
    user_permissions = PermissionSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "password2",
            "user_type",
            "user_firstname",
            "user_lastname",
            "user_father_name",
            "user_specialization",
            "user_public_phone",
            "user_private_phone",
            "user_birthdate",
            "user_gender",
            "user_address",
            "user_citizenship",
            "user_telegram",
            "user_salary_percent",
            "user_salary_child_percent",
            "user_color",
            "user_has_car",
            "user_on_place",
            "user_is_active",
            "user_schedule",
            "groups",
            "user_permissions",
        ]
        extra_kwargs = {"user_father_name": {"required": False}}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["user_gender"] = instance.get_user_gender_display()
        return data

    def create(self, validated_data):
        user = User(
            username=validated_data.get("username"),
            user_firstname=validated_data.get("user_firstname"),
            user_lastname=validated_data.get("user_lastname"),
            user_father_name=validated_data.get("user_father_name", None),
            user_birthdate=validated_data.get("user_birthdate"),
            user_gender=validated_data.get("user_gender"),
            user_address=validated_data.get("user_address"),
            user_citizenship=validated_data.get("user_citizenship"),
            user_telegram=validated_data.get("user_telegram"),
            user_salary_percent=validated_data.get("user_salary_percent"),
            user_salary_child_percent=validated_data.get("user_salary_child_percent"),
            user_color=validated_data.get("user_color", None),
            user_has_car=validated_data.get("user_has_car"),
            user_on_place=validated_data.get("user_on_place"),
            user_is_active=True,
            is_active=True,
            is_staff=False,
        )
        password = validated_data["password"]
        password2 = validated_data["password2"]
        if password != password2:
            raise ValidationError({"password": "Password did not match"})

        user_type_data = validated_data.pop("user_type")
        user_type_instance = User_Type.objects.get(
            pk=user_type_data.get("user_type_id")
        )
        user.user_type = user_type_instance

        user.set_password(password)
        user.save()

        group_data = validated_data.pop("groups")
        group_list = Group.objects.filter(pk__in=[ids["id"] for ids in group_data])
        user.groups.set(group_list)

        permissions_data = validated_data.pop("user_permissions", None)
        if permissions_data:
            perms_list = Permission.objects.filter(
                pk__in=[ids["id"] for ids in permissions_data]
            )
            user.user_permissions.set(perms_list)

        user_schedule_data = validated_data.pop("user_schedule")
        user_schedules = [
            UserSchedule(user=user, **schedule) for schedule in user_schedule_data
        ]
        UserSchedule.objects.bulk_create(user_schedules)

        public_phone_data = validated_data.pop("user_public_phone", None)
        if public_phone_data:
            user_public_phones = [
                User_Public_Phone(user=user, **phones) for phones in public_phone_data
            ]
            User_Public_Phone.objects.bulk_create(user_public_phones)

        private_phone_data = validated_data.pop("user_private_phone")
        user_private_phones = [
            User_Private_Phone(user=user, **phones) for phones in private_phone_data
        ]
        User_Private_Phone.objects.bulk_create(user_private_phones)

        specialization_data = validated_data.pop("user_specialization", None)
        if specialization_data:
            spec_list = Specialization.objects.filter(
                specialization_id__in=[
                    ids["specialization_id"] for ids in specialization_data
                ]
            )
            user.user_specialization.set(spec_list)
        return user


class UserSerializerData(serializers.ModelSerializer):
    # Сериализация общих данных об доктора

    user_type = UserTypeInsertSerializer(required=False)
    user_public_phone = UserPublicPhoneSerializer(many=True, required=False)
    user_private_phone = UserPrivatePhoneSerializer(many=True, required=False)
    user_specialization = UserSpecializationSerializer(many=True, required=False)
    user_birthdate = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"], required=False
    )
    user_image = serializers.SerializerMethodField("get_user_image")
    user_schedule = ScheduleSerializer(many=True, required=False)
    groups = GroupSerializer(many=True, required=False)
    user_permissions = PermissionSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "user_type",
            "user_firstname",
            "user_lastname",
            "user_father_name",
            "user_public_phone",
            "user_private_phone",
            "user_specialization",
            "user_birthdate",
            "user_citizenship",
            "user_gender",
            "user_image",
            "user_salary_percent",
            "user_salary_child_percent",
            "user_is_active",
            "user_has_car",
            "user_color",
            "user_on_place",
            "user_telegram",
            "user_address",
            "groups",
            "user_permissions",
            "user_schedule",
            "updated_at",
            "created_at",
        ]
        extra_kwargs = {
            "username": {"read_only": True},
            "user_firstname": {"required": False},
            "user_lastname": {"required": False},
            "user_father_name": {"required": False},
            "user_citizenship": {"required": False},
            "user_birthdate": {"required": False},
            "user_salary_percent": {"required": False},
            "user_salary_child_percent": {"required": False},
            "user_is_active": {"required": False},
            "user_color": {"required": False},
            "user_on_place": {"required": False},
            "user_has_car": {"required": False},
            "user_telegram": {"required": False},
            "user_address": {"required": False},
            "updated_at": {"read_only": True},
            "created_at": {"read_only": True},
        }

    def get_user_image(self, obj):
        try:
            request = self.context.get("request")
            user_image = request.build_absolute_uri(obj.user_image.url)
            return user_image
        except:
            return None

    def to_representation(self, instance):
        data = super(UserSerializerData, self).to_representation(instance)
        data["user_gender"] = instance.get_user_gender_display()
        current_user = self.context.get("current_user")
        private_fields = [
            "user_type",
            "user_private_phone",
            "user_salary_percent",
            "user_salary_child_percent",
            "user_address",
            "user_telegram",
        ]
        only_for_admin_fields = ["username", "groups", "user_permissions"]

        for field, field_value in sorted(data.items()):

            if field in private_fields and current_user != instance:
                if not current_user.has_perm("user.view_user_private_info"):
                    data.pop(field)

            if field in only_for_admin_fields:
                if not current_user.has_perm("user.view_user_private_info"):
                    data.pop(field)

            if field == "user_schedule" and current_user != instance:
                if not current_user.has_perm("user.view_user_schedule"):
                    data.pop(field)
        return data

    def to_internal_value(self, data):
        current_user = self.context.get("current_user")
        private_fields = [
            "username",
            "user_type",
            "groups",
            "user_permissions",
            "user_salary_percent",
            "user_salary_child_percent",
        ]
        errors = {}

        for field, field_value in sorted(data.items()):

            if field in private_fields:
                if not current_user.has_perm("user.change_user_private_info"):
                    errors[field] = ["This field is not allowed to change"]

            if field == "user_schedule":
                if not current_user.has_perm("user.change_user_schedule"):
                    errors[field] = ["This field is not allowed to change"]

            if errors:
                raise ValidationError(errors)

        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        # Обновление общих данных доктора
        instance.user_firstname = validated_data.get(
            "user_firstname", instance.user_firstname
        )
        instance.user_lastname = validated_data.get(
            "user_lastname", instance.user_lastname
        )
        instance.user_father_name = validated_data.get(
            "user_father_name", instance.user_father_name
        )
        instance.user_birthdate = validated_data.get(
            "user_birthdate", instance.user_birthdate
        )
        instance.user_citizenship = validated_data.get(
            "user_citizenship", instance.user_citizenship
        )
        instance.user_gender = validated_data.get("user_gender", instance.user_gender)
        instance.user_salary_percent = validated_data.get(
            "user_salary_percent", instance.user_salary_percent
        )
        instance.user_salary_child_percent = validated_data.get(
            "user_salary_child_percent", instance.user_salary_child_percent
        )
        instance.user_telegram = validated_data.get(
            "user_telegram", instance.user_telegram
        )
        instance.user_address = validated_data.get(
            "user_address", instance.user_address
        )
        instance.user_color = validated_data.get("user_color", instance.user_color)

        user_is_active = validated_data.get("user_is_active")

        if user_is_active == "true":
            user_is_active = True
        elif user_is_active == "false":
            user_is_active = False
        instance.user_is_active = user_is_active
        user_on_place = validated_data.get("user_on_place")
        if user_on_place == "true":
            user_on_place = True
        elif user_on_place == "false":
            user_on_place = False
        instance.user_on_place = user_on_place
        user_has_car = validated_data.get("user_has_car")
        if user_has_car == "true":
            user_has_car = True
        elif user_has_car == "false":
            user_has_car = False
        instance.user_has_car = user_has_car

        user_type_data = validated_data.pop("user_type", None)
        if user_type_data:
            user_type_instance = User_Type.objects.get(
                pk=user_type_data.get("user_type_id")
            )
            instance.user_type = user_type_instance

        public_phone_data = validated_data.pop("user_public_phone", None)
        if public_phone_data:
            deleted_public_phones = User_Public_Phone.objects.filter(
                ~Q(
                    pk__in=[
                        ids["user_phone_id"]
                        for ids in public_phone_data
                        if "user_phone_id" in ids.keys()
                    ]
                ),
                user_id=instance.pk,
            )
            if deleted_public_phones.exists():
                deleted_public_phones.delete()

            updated_public_phones = [
                User_Public_Phone(user_id=instance.pk, **phones)
                for phones in public_phone_data
                if "user_phone_id" in phones.keys()
            ]
            User_Public_Phone.objects.bulk_update(
                updated_public_phones, ["public_phone"]
            )

            new_public_phones = [
                User_Public_Phone(user_id=instance.pk, **phones)
                for phones in public_phone_data
                if "user_phone_id" not in phones.keys()
            ]
            User_Public_Phone.objects.bulk_create(new_public_phones)

        private_phone_data = validated_data.pop("user_private_phone", None)
        if private_phone_data:
            deleted_private_phones = User_Private_Phone.objects.filter(
                ~Q(
                    pk__in=[
                        ids["user_phone_id"]
                        for ids in private_phone_data
                        if "user_phone_id" in ids.keys()
                    ]
                ),
                user_id=instance.pk,
            )
            if deleted_private_phones.exists():
                deleted_private_phones.delete()

            updated_private_phones = [
                User_Private_Phone(user_id=instance.pk, **phones)
                for phones in private_phone_data
                if "user_phone_id" in phones.keys()
            ]
            User_Private_Phone.objects.bulk_update(
                updated_private_phones, ["private_phone"]
            )

            new_private_phones = [
                User_Private_Phone(user_id=instance.pk, **phones)
                for phones in private_phone_data
                if "user_phone_id" not in phones.keys()
            ]
            User_Private_Phone.objects.bulk_create(new_private_phones)

            # Обновление специализаций доктора
        specialization_data = validated_data.pop("user_specialization", None)
        if specialization_data:
            instance.user_specialization.clear()
            spec_list = Specialization.objects.filter(
                specialization_id__in=[
                    ids["specialization_id"] for ids in specialization_data
                ]
            )
            instance.user_specialization.set(spec_list)

        group_data = validated_data.pop("groups", None)
        if group_data:
            instance.groups.clear()
            group_list = Group.objects.filter(pk__in=[ids["id"] for ids in group_data])
            instance.groups.set(group_list)

        permissions_data = validated_data.pop("user_permissions", None)
        if permissions_data:
            instance.user_permissions.clear()
            perms_list = Permission.objects.filter(
                pk__in=[ids["id"] for ids in permissions_data]
            )
            instance.user_permissions.set(perms_list)

        user_schedule_data = validated_data.pop("user_schedule", None)
        if user_schedule_data:
            for schedule_data in user_schedule_data:
                schedule_id = schedule_data.pop("schedule_id")
                schedule_instance = UserSchedule.objects.get(
                    pk=schedule_id, user=instance
                )
                schedule_instance.work_start_time = schedule_data.get(
                    "work_start_time", schedule_instance.work_start_time
                )
                schedule_instance.work_end_time = schedule_data.get(
                    "work_end_time", schedule_instance.work_end_time
                )
                schedule_instance.lunch_start_time = schedule_data.get(
                    "lunch_start_time", schedule_instance.lunch_start_time
                )
                schedule_instance.lunch_end_time = schedule_data.get(
                    "lunch_end_time", schedule_instance.lunch_end_time
                )
                schedule_instance.is_working = schedule_data.get(
                    "is_working", schedule_instance.is_working
                )
                schedule_instance.one_time_update = schedule_data.get(
                    "one_time_update", schedule_instance.one_time_update
                )
                schedule_instance.save()

        instance.save()
        return instance


class UserPasswordUpdateSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        max_length=50, min_length=8, write_only=True, required=False
    )
    password = serializers.CharField(max_length=50, min_length=8, write_only=True)
    password2 = serializers.CharField(max_length=50, min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ["old_password", "password", "password2"]
        extra_kwargs = {"old_password": {"required": False}}

    def update(self, instance, validated_data):
        current_user = self.context.get("current_user")
        if current_user.has_perm("user.change_password"):
            password = validated_data["password"]
            password2 = validated_data["password2"]
            if password != password2:
                raise ValidationError({"password": "Password did not match"})

            instance.set_password(password)
            instance.save()
        else:
            if current_user == instance:
                if not instance.check_password(validated_data["old_password"]):
                    raise ValidationError({"old_password": ["Wrong password."]})
                else:
                    password = validated_data["password"]
                    password2 = validated_data["password2"]
                    if password != password2:
                        raise ValidationError({"password": "Password did not match"})

                    instance.set_password(password)
                    instance.save()
            else:
                raise ValidationError({"Sorry you have no access to change a password"})

        return instance


class UserTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = User_Type
        fields = [
            "user_type_id",
            "type_text",
            "type_text_ru",
            "type_text_en",
            "type_text_uz",
        ]
        extra_kwargs = {"type_text": {"required": False}}


class UserSalarySerializer(serializers.ModelSerializer):
    salary_for_user = NestedDoctorSerializer(read_only=True)
    salary_work = WorkSerializer(read_only=True)
    client_id = serializers.ReadOnlyField()
    client_full_name = serializers.ReadOnlyField()

    class Meta:
        model = UserSalary
        fields = [
            "salary_id",
            "client_id",
            "client_full_name",
            "salary_for_user",
            "salary_action",
            "salary_card",
            "salary_work",
            "salary_work_type",
            "salary_action_price",
            "salary_work_price",
            "salary_amount",
            "salary_is_paid",
            "updated_at",
            "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.salary_card and instance.salary_card.client:
            data["client_id"] = instance.salary_card.client.client_id
            data["client_full_name"] = instance.salary_card.client.full_name()
        else:
            data["client_id"] = None
            data["client_full_name"] = None
        return data


class UserListSerializer(serializers.ModelSerializer):
    user_type = UserTypeSerializer(required=False)
    user_public_phone = UserPublicPhoneSerializer(many=True, required=False)
    user_private_phone = UserPrivatePhoneSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "user_firstname",
            "user_lastname",
            "user_type",
            "user_public_phone",
            "user_private_phone",
        ]


class UserBriefListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "id",
            "user_type",
            "user_firstname",
            "user_lastname",
            "user_father_name",
            "user_color",
        )


class UserImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    user_image = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ["id", "user_image"]


class UserFlutterSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    username = serializers.CharField()


class UserScheduleSerializer(serializers.ModelSerializer):
    work_start_time = serializers.TimeField(format="%H:%M")
    work_end_time = serializers.TimeField(format="%H:%M")
    lunch_start_time = serializers.TimeField(format="%H:%M")
    lunch_end_time = serializers.TimeField(format="%H:%M")

    class Meta:
        model = UserSchedule
        fields = [
            "day",
            "work_start_time",
            "work_end_time",
            "lunch_start_time",
            "lunch_end_time",
            "is_working",
        ]


class UserScheduleListSerializer(serializers.ModelSerializer):
    user_schedule = UserScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "user_firstname",
            "user_lastname",
            "user_father_name",
            "user_color",
            "user_schedule",
        ]


class UserSalaryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSalary
        fields = "__all__"
