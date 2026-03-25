from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.client import filtersets
from apps.client.api import serializers
from apps.client.models import CashbackEntry, Client, Client_Public_Phone, ClientAnamnesis
from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.credit.models import Credit
from apps.expenses.models import FinancialReport
from apps.medcard.models import MedicalCard
from apps.notifications.models import Notification
from apps.reservation.models import Reservation
from apps.transaction.models import Transaction

# from apps.client.signals import client_signal


def get_current_local_date():
    current_time = timezone.now()
    if timezone.is_aware(current_time):
        return timezone.localtime(current_time).date()
    return current_time.date()


def get_mobile_client_or_error(user):
    client = getattr(user, "client_user", None)
    if not client:
        raise serializers.ValidationError(_("Current user is not linked to a client"))
    if not client.referral_code:
        client.save(update_fields=["referral_code"])
    return client


@extend_schema(tags=["clients"])
class ClientViewSet(BaseViewSet):
    queryset = Client.objects.prefetch_related("client_public_phone").order_by(
        "-client_last_viewed_at"
    )
    pagination_class = BasePagination
    filterset_class = filtersets.ClientFilter
    permission_classes = (AccessPermissions,)

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.ClientSerializer
        elif self.action == "list":
            return serializers.ClientListSerializer
        return serializers.ClientSerializerData

    def get_object(self):
        instance = super().get_object()
        instance.client_last_viewed_at = timezone.now()
        instance.save(update_fields=["client_last_viewed_at"])
        return instance

    def partial_update(self, request, *args, **kwargs):
        instance = super().get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        data["client_public_phone"] = serializers.ClientPublicPhoneSerializer(
            Client_Public_Phone.objects.filter(client_id=instance), many=True
        ).data
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=["clients_flutter"])
class ClientFlutterViewSet(BaseViewSet):
    queryset = Client.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.ClientFlutterCreateSerializer
        if self.action == "retrieve":
            return serializers.ClientFlutterDataSerializer
        if self.action == "partial_update":
            return serializers.ClientFlutterDataSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        # client_signal.send(sender=Client, instance=obj, created=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["clients"])
class MergeClientsView(generics.GenericAPIView):
    queryset = Client.objects.all()
    serializer_class = serializers.MergeClientSerializer

    def post(self, request, *args, **kwargs):
        try:
            instance = super().get_object()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            duplicate_ids = data.get("duplicate_ids")

            duplicate_clients = Client.objects.filter(client_id__in=duplicate_ids)
            for duplicate_client in duplicate_clients:
                instance.client_balance += duplicate_client.client_balance
                instance.save(update_fields=["client_balance"])

            public_phones = Client_Public_Phone.objects.filter(
                client_id__in=duplicate_ids
            )
            instance_public_phones = Client_Public_Phone.objects.filter(client=instance)

            if public_phones.exists():
                for d_public_phone in public_phones:
                    for i_public_phone in instance_public_phones:
                        if d_public_phone.public_phone == i_public_phone.public_phone:
                            d_public_phone.delete()

                public_phones.update(client=instance)

            medical_cards = MedicalCard.objects.filter(client_id__in=duplicate_ids)
            if medical_cards.exists():
                medical_cards.update(client=instance)

            credits_ = Credit.objects.filter(credit_client_id__in=duplicate_ids)
            if credits_.exists():
                credits_.update(credit_client=instance)

            financial_reports = FinancialReport.objects.filter(
                report_for_client_id__in=duplicate_ids
            )
            if financial_reports.exists():
                financial_reports.update(report_for_client=instance)

            reservations = Reservation.objects.filter(
                reservation_client_id__in=duplicate_ids
            )
            if reservations.exists():
                reservations.update(reservation_client=instance)

            transactions = Transaction.objects.filter(
                transaction_client_id__in=duplicate_ids
            )

            if transactions.exists():
                transactions.update(transaction_client=instance)

            transactions_receivers = Transaction.objects.filter(
                transaction_receiver_id__in=duplicate_ids
            )

            if transactions.exists():
                transactions_receivers.update(transaction_receiver=instance)

            Client.objects.filter(pk__in=duplicate_ids).delete()

            return Response("ok", status=status.HTTP_200_OK)

        except Exception as e:
            raise e


@extend_schema(tags=["clients_anamnesis"])
class ClientAnamnesisViewSet(BaseViewSet):
    queryset = ClientAnamnesis.objects.select_related("client").order_by("-created_at")
    pagination_class = BasePagination
    filterset_class = filtersets.ClientAnamnesisFilter
    permission_classes = (AccessPermissions,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return serializers.ClientAnamnesisDetailSerializer
        return serializers.ClientAnamnesisSerializer


@extend_schema(tags=["mobile_client"])
class MobileMeView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return get_mobile_client_or_error(self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return serializers.MobileMeUpdateSerializer
        return serializers.MobileMeSerializer

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.MobileMeSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = serializers.MobileMeSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["mobile_client"])
class MobileLoyaltyView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileReferralInfoSerializer

    def get_object(self):
        return get_mobile_client_or_error(self.request.user)


@extend_schema(tags=["mobile_client"])
class MobileCashbackHistoryView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileCashbackEntrySerializer
    pagination_class = BasePagination

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return CashbackEntry.objects.none()
        return CashbackEntry.objects.filter(client=client).select_related(
            "related_client"
        )


@extend_schema(tags=["mobile_client"])
class MobileApplyReferralCodeView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ApplyReferralCodeSerializer

    def post(self, request, *args, **kwargs):
        client = get_mobile_client_or_error(request.user)
        serializer = self.get_serializer(data=request.data, context={"client": client})
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        response_serializer = serializers.MobileReferralInfoSerializer(client)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["mobile_client"])
class MobileStatusView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileStatusSerializer

    def get_object(self):
        return get_mobile_client_or_error(self.request.user)


@extend_schema(tags=["mobile_client"])
class MobileDashboardView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileDashboardSerializer

    def get(self, request, *args, **kwargs):
        client = get_mobile_client_or_error(request.user)

        active_reservations = Reservation.objects.filter(
            reservation_client=client,
            cancelled=False,
            reservation_date__gte=get_current_local_date(),
        )
        active_treatments = MedicalCard.objects.filter(
            client=client,
            deleted=False,
            card_is_cancelled=False,
            card_is_done=False,
        )
        unread_notifications = Notification.objects.filter(
            notification_receiver=request.user,
            is_read=False,
        ).count()
        next_reservation = (
            active_reservations.order_by("reservation_date", "reservation_start_time")
            .select_related("reservation_doctor", "reservation_work")
            .first()
        )

        data = {
            "profile": serializers.MobileMeSerializer(client).data,
            "counters": {
                "active_reservations": active_reservations.count(),
                "active_treatments": active_treatments.count(),
                "unread_notifications": unread_notifications,
                "referrals_count": client.referred_clients.count(),
            },
            "loyalty": serializers.MobileReferralInfoSerializer(client).data,
            "next_reservation": (
                {
                    "reservation_id": next_reservation.reservation_id,
                    "doctor_name": next_reservation.reservation_doctor.full_name()
                    if next_reservation.reservation_doctor
                    else None,
                    "service_title": next_reservation.reservation_work.work_title
                    if next_reservation.reservation_work
                    else None,
                    "date": next_reservation.reservation_date.strftime("%d-%m-%Y"),
                    "start_time": next_reservation.reservation_start_time.strftime("%H:%M"),
                    "end_time": next_reservation.reservation_end_time.strftime("%H:%M"),
                }
                if next_reservation
                else None
            ),
        }
        serializer = self.get_serializer(instance=data)
        return Response(serializer.data, status=status.HTTP_200_OK)
