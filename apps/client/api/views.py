from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from apps.client import filtersets
from apps.client.api import serializers
from apps.client.models import Client, Client_Public_Phone, ClientAnamnesis
from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.credit.models import Credit
from apps.expenses.models import FinancialReport
from apps.medcard.models import MedicalCard
from apps.reservation.models import Reservation
from apps.transaction.models import Transaction

# from apps.client.signals import client_signal


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
