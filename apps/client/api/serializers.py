from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.client.api.nested_serializer import NestedClientSerializer
from apps.client.loyalty import (
    apply_referral_code,
    build_tier_requirements,
    get_cashback_rate,
)
from apps.client.models import CashbackEntry, Client, Client_Public_Phone, ClientAnamnesis
from apps.credit.api.serializers import CreditSerializer
from apps.user.api.serializers import UserFlutterSerializer
from apps.user.models import User, User_Public_Phone


class PatientSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(required=False)

    class Meta:
        model = Client
        fields = ["client_id", "client_firstname", "client_lastname"]
        extra_kwargs = {
            "client_firstname": {"read_only": True},
            "client_lastname": {"read_only": True},
        }


class ClientPublicPhoneSerializer(serializers.ModelSerializer):
    client_phone_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = Client_Public_Phone
        fields = ["client_phone_id", "public_phone"]


class ClientSerializer(serializers.ModelSerializer):
    # Добавление клиента
    client_public_phone = ClientPublicPhoneSerializer(many=True, required=False)
    client_birthdate = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )

    class Meta:
        model = Client
        fields = [
            "client_id",
            "client_firstname",
            "client_lastname",
            "client_father_name",
            "client_birthdate",
            "client_gender",
            "client_citizenship",
            "client_public_phone",
            "client_telegram",
            "client_address",
            "note",
            "client_type",
        ]
        extra_kwargs = {"client_address": {"required": False}}

    def create(self, validated_data):
        user = User()
        user.save()

        client = Client(
            client_user=user,
            client_firstname=validated_data["client_firstname"],
            client_lastname=validated_data["client_lastname"],
            client_father_name=validated_data.get("client_father_name", None),
            client_birthdate=validated_data["client_birthdate"],
            client_gender=validated_data["client_gender"],
            client_citizenship=validated_data["client_citizenship"],
            client_telegram=validated_data.get("client_telegram", None),
            client_address=validated_data.get("client_address", None),
            note=validated_data.get("note", None),
            client_type=validated_data["client_type"],
        )
        client.save()

        public_phone_data = validated_data.pop("client_public_phone", None)
        if public_phone_data:
            client_public_phones = [
                Client_Public_Phone(client_id=client.pk, **phones)
                for phones in public_phone_data
            ]
            Client_Public_Phone.objects.bulk_create(client_public_phones)
            User_Public_Phone.objects.create(
                user=user, public_phone=public_phone_data[0]["public_phone"]
            )
        return client

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["client_gender"] = instance.get_client_gender_display()
        data["client_type"] = instance.get_client_type_display()
        return data


class ClientSerializerData(serializers.ModelSerializer):
    # Сериализация общих данных о клиенте

    client_public_phone = ClientPublicPhoneSerializer(many=True, required=False)
    client_birthdate = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"], required=False
    )
    credit_client = CreditSerializer(read_only=True, many=True)

    class Meta:
        model = Client
        fields = [
            "client_id",
            "client_firstname",
            "client_lastname",
            "client_father_name",
            "client_birthdate",
            "client_public_phone",
            "credit_client",
            "client_citizenship",
            "client_gender",
            "client_telegram",
            "client_address",
            "client_type",
            "client_balance",
            "note",
            "updated_at",
            "created_at",
        ]
        extra_kwargs = {
            "client_firstname": {"required": False},
            "client_lastname": {"required": False},
            "client_father_name": {"required": False},
            "client_birthdate": {"required": False},
            "client_citizenship": {"required": False},
            "client_telegram": {"required": False},
            "client_address": {"required": False},
            "client_gender": {"required": False},
            "client_balance": {"read_only": True},
            "client_type": {"required": False},
            "updated_at": {"read_only": True},
            "created_at": {"read_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["client_gender"] = instance.get_client_gender_display()
        data["client_type"] = instance.get_client_type_display()
        return data

    def update(self, instance, validated_data):
        # Обновление контактных данных клиента

        public_phone_data = validated_data.pop("client_public_phone", None)
        if public_phone_data:
            deleted_public_phones = Client_Public_Phone.objects.filter(
                ~Q(
                    pk__in=[
                        ids["client_phone_id"]
                        for ids in public_phone_data
                        if "client_phone_id" in ids.keys()
                    ]
                ),
                client_id=instance.pk,
            )
            if deleted_public_phones.exists():
                deleted_public_phones.delete()

            for phones in public_phone_data:
                if "client_phone_id" in phones.keys():
                    public_phone = Client_Public_Phone.objects.get(
                        pk=phones.get("client_phone_id")
                    )
                    public_phone.public_phone = phones.get("public_phone")
                    public_phone.save()
                else:
                    public_phone = Client_Public_Phone(
                        client_id=instance.pk, public_phone=phones.get("public_phone")
                    )
                    public_phone.save()

        instance.client_firstname = validated_data.get(
            "client_firstname", instance.client_firstname
        )
        instance.client_lastname = validated_data.get(
            "client_lastname", instance.client_lastname
        )
        instance.client_father_name = validated_data.get(
            "client_father_name", instance.client_father_name
        )
        instance.client_birthdate = validated_data.get(
            "client_birthdate", instance.client_birthdate
        )
        instance.client_citizenship = validated_data.get(
            "client_citizenship", instance.client_citizenship
        )
        instance.client_gender = validated_data.get(
            "client_gender", instance.client_gender
        )
        instance.client_telegram = validated_data.get(
            "client_telegram", instance.client_telegram
        )
        instance.client_address = validated_data.get(
            "client_address", instance.client_address
        )
        instance.client_type = validated_data.get("client_type", instance.client_type)
        instance.note = validated_data.get("note", instance.note)
        instance.save()
        return instance


class ClientListSerializer(serializers.ModelSerializer):
    client_public_phone = ClientPublicPhoneSerializer(many=True, required=False)
    client_birthdate = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )

    class Meta:
        model = Client
        fields = [
            "client_id",
            "client_firstname",
            "client_lastname",
            "client_birthdate",
            "client_public_phone",
            "client_gender",
            "note",
            "client_type",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["client_gender"] = instance.get_client_gender_display()
        data["client_type"] = instance.get_client_type_display()
        return data


class ClientFlutterCreateSerializer(serializers.ModelSerializer):
    # Добавление клиента
    client_birthdate = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    client_public_phone = ClientPublicPhoneSerializer(many=True, read_only=True)
    client_user = serializers.SerializerMethodField("get_client_user")

    class Meta:
        model = Client
        fields = [
            "client_id",
            "user_id",
            "client_user",
            "client_firstname",
            "client_lastname",
            "client_father_name",
            "client_birthdate",
            "client_gender",
            "client_citizenship",
            "client_public_phone",
            "client_address",
            "created_at",
        ]
        extra_kwargs = {
            "client_address": {"required": False},
            "created_at": {"read_only": True},
        }

    def validate(self, attrs):
        user = attrs["user_id"]

        if not user.user_is_active:
            raise ValidationError("User is not active!")

        return attrs

    def get_client_user(self, obj):
        user = User.objects.get(client_user=obj)
        serializer = UserFlutterSerializer(user)
        return serializer.data

    def create(self, validated_data):
        user = validated_data["user_id"]
        client = Client(
            client_user=user,
            client_firstname=validated_data["client_firstname"],
            client_lastname=validated_data["client_lastname"],
            client_father_name=validated_data.get("client_father_name", None),
            client_birthdate=validated_data["client_birthdate"],
            client_gender=validated_data["client_gender"],
            client_citizenship=validated_data["client_citizenship"],
            client_address=validated_data.get("client_address", None),
            client_type="Basic",
        )
        client.save()

        public_phone = User_Public_Phone.objects.filter(user=user).first()
        phone = Client_Public_Phone(
            client=client, public_phone=public_phone.public_phone
        )
        phone.save()
        return client


class ClientFlutterDataSerializer(serializers.ModelSerializer):
    client_birthdate = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"], required=False
    )
    client_public_phone = ClientPublicPhoneSerializer(many=True, required=False)
    client_user = UserFlutterSerializer(required=False)

    class Meta:
        model = Client
        fields = [
            "client_id",
            "client_user",
            "client_firstname",
            "client_lastname",
            "client_father_name",
            "client_birthdate",
            "client_gender",
            "client_balance",
            "client_citizenship",
            "client_public_phone",
            "client_address",
            "created_at",
        ]
        extra_kwargs = {
            "client_firstname": {"required": False},
            "client_lastname": {"required": False},
            "client_father_name": {"required": False},
            "client_birthdate": {"required": False},
            "client_citizenship": {"required": False},
            "client_address": {"required": False},
            "client_gender": {"required": False},
            "created_at": {"read_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["client_gender"] = instance.get_client_gender_display()
        return data

    def update(self, instance, validated_data):
        user = User.objects.get(client_user=instance)

        client_user_data = validated_data.pop("client_user", None)
        if client_user_data:
            user.username = client_user_data["username"]
            user.save()

        public_phone_data = validated_data.pop("client_public_phone", None)
        if public_phone_data:
            for phones in public_phone_data:
                public_phone = Client_Public_Phone.objects.get(
                    pk=phones.get("client_phone_id")
                )
                public_phone.public_phone = phones.get("public_phone")
                public_phone.save()
                user_phone = User_Public_Phone.objects.filter(user=user)
                user_phone.public_phone = phones.get("public_phone")
                user_phone.save()

        instance.client_firstname = validated_data.get(
            "client_firstname", instance.client_firstname
        )
        instance.client_lastname = validated_data.get(
            "client_lastname", instance.client_lastname
        )
        instance.client_father_name = validated_data.get(
            "client_father_name", instance.client_father_name
        )
        instance.client_birthdate = validated_data.get(
            "client_birthdate", instance.client_birthdate
        )
        instance.client_citizenship = validated_data.get(
            "client_citizenship", instance.client_citizenship
        )
        instance.client_gender = validated_data.get(
            "client_gender", instance.client_gender
        )
        instance.client_address = validated_data.get(
            "client_address", instance.client_address
        )
        instance.save()
        return instance


class MergeClientSerializer(serializers.Serializer):
    duplicate_ids = serializers.ListSerializer(child=serializers.IntegerField())


class ClientAnamnesisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAnamnesis
        fields = [
            "id",
            "client",
            "contact_reason",
            "treatment_history",
            "hepatitis",
            "hiv",
        ]


class ClientAnamnesisDetailSerializer(serializers.ModelSerializer):
    client = NestedClientSerializer(read_only=True)

    class Meta:
        model = ClientAnamnesis
        fields = [
            "id",
            "client",
            "contact_reason",
            "treatment_history",
            "hepatitis",
            "hiv",
        ]


def serialize_datetime(value):
    if not value:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return timezone.localtime(value).strftime("%d-%m-%Y %H:%M")


class MobileMeSerializer(serializers.ModelSerializer):
    phone = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    loyalty_tier_label = serializers.CharField(source="get_loyalty_tier_display", read_only=True)

    class Meta:
        model = Client
        fields = [
            "client_id",
            "username",
            "full_name",
            "client_firstname",
            "client_lastname",
            "client_father_name",
            "client_birthdate",
            "client_gender",
            "client_citizenship",
            "client_address",
            "client_telegram",
            "client_type",
            "client_balance",
            "cashback_balance",
            "referral_code",
            "loyalty_tier",
            "loyalty_tier_label",
            "total_spent_amount",
            "note",
            "phone",
            "created_at",
        ]

    def get_phone(self, obj):
        phone = obj.client_public_phone.first()
        return phone.public_phone if phone else None

    def get_full_name(self, obj):
        return obj.full_name()

    def get_username(self, obj):
        return obj.client_user.username if obj.client_user else None

    def get_created_at(self, obj):
        return serialize_datetime(obj.created_at)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["client_gender"] = instance.get_client_gender_display()
        data["client_type"] = instance.get_client_type_display()
        data["cashback_percent"] = round(get_cashback_rate(instance.loyalty_tier) * 100, 2)
        return data


class MobileMeUpdateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=False, allow_blank=False)

    class Meta:
        model = Client
        fields = [
            "client_firstname",
            "client_lastname",
            "client_father_name",
            "client_birthdate",
            "client_gender",
            "client_citizenship",
            "client_address",
            "client_telegram",
            "note",
            "phone",
        ]
        extra_kwargs = {
            "client_firstname": {"required": False},
            "client_lastname": {"required": False},
            "client_father_name": {"required": False},
            "client_birthdate": {"required": False},
            "client_gender": {"required": False},
            "client_citizenship": {"required": False},
            "client_address": {"required": False},
            "client_telegram": {"required": False},
            "note": {"required": False},
        }

    def update(self, instance, validated_data):
        phone = validated_data.pop("phone", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if phone:
            public_phone = instance.client_public_phone.first()
            if public_phone:
                public_phone.public_phone = phone
                public_phone.save(update_fields=["public_phone"])
            else:
                Client_Public_Phone.objects.create(client=instance, public_phone=phone)

            if instance.client_user:
                user_public_phone = User_Public_Phone.objects.filter(
                    user=instance.client_user
                ).first()
                if user_public_phone:
                    user_public_phone.public_phone = phone
                    user_public_phone.save(update_fields=["public_phone"])
                else:
                    User_Public_Phone.objects.create(
                        user=instance.client_user, public_phone=phone
                    )
        return instance


class MobileReferralInfoSerializer(serializers.ModelSerializer):
    referred_by_name = serializers.SerializerMethodField()
    referrals_count = serializers.SerializerMethodField()
    loyalty_tier_label = serializers.CharField(source="get_loyalty_tier_display", read_only=True)

    class Meta:
        model = Client
        fields = [
            "client_id",
            "referral_code",
            "referred_by",
            "referred_by_name",
            "referrals_count",
            "loyalty_tier",
            "loyalty_tier_label",
            "cashback_balance",
            "total_spent_amount",
        ]

    def get_referred_by_name(self, obj):
        return obj.referred_by.full_name() if obj.referred_by else None

    def get_referrals_count(self, obj):
        return obj.referred_clients.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["cashback_percent"] = round(get_cashback_rate(instance.loyalty_tier) * 100, 2)
        return data


class MobileCashbackEntrySerializer(serializers.ModelSerializer):
    entry_type_label = serializers.CharField(source="get_entry_type_display", read_only=True)
    related_client_name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = CashbackEntry
        fields = [
            "entry_id",
            "entry_type",
            "entry_type_label",
            "amount",
            "balance_after",
            "note",
            "related_client_name",
            "created_at",
        ]

    def get_related_client_name(self, obj):
        return obj.related_client.full_name() if obj.related_client else None

    def get_created_at(self, obj):
        return serialize_datetime(obj.created_at)


class ApplyReferralCodeSerializer(serializers.Serializer):
    referral_code = serializers.CharField()

    def save(self, **kwargs):
        client = self.context["client"]
        return apply_referral_code(
            client=client,
            referral_code=self.validated_data["referral_code"],
        )


class MobileStatusSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    current_tier_label = serializers.CharField(source="get_loyalty_tier_display", read_only=True)
    cashback_percent = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "client_id",
            "full_name",
            "loyalty_tier",
            "current_tier_label",
            "cashback_balance",
            "referral_code",
            "progress",
            "cashback_percent",
        ]

    def get_full_name(self, obj):
        return obj.full_name()

    def get_cashback_percent(self, obj):
        return round(get_cashback_rate(obj.loyalty_tier) * 100, 2)

    def get_progress(self, obj):
        progress = build_tier_requirements(obj)
        if progress["next_tier"]:
            progress["next_tier_label"] = dict(obj._meta.get_field("loyalty_tier").choices).get(
                progress["next_tier"], progress["next_tier"]
            )
        else:
            progress["next_tier_label"] = None
        return progress


class MobileDashboardSerializer(serializers.Serializer):
    profile = serializers.DictField()
    counters = serializers.DictField()
    loyalty = serializers.DictField()
    next_reservation = serializers.DictField(allow_null=True)
