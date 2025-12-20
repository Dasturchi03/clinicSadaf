from rest_framework.decorators import action

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.transaction import filtersets
from apps.transaction.api import serializers
from apps.transaction.models import Transaction


class TransactionViewSet(BaseViewSet):
    queryset = Transaction.objects.order_by("-transaction_created_at")
    pagination_class = BasePagination
    filterset_class = filtersets.TransactionFilterSet
    permission_classes = (AccessPermissions,)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return serializers.TransactionSerializer
        elif self.action == "credits_pay":
            return serializers.TransactionCreditPaySerializer
        elif self.action == "clients_balance":
            return serializers.TransactionClientBalanceSerializer
        elif self.action == "clients_refund":
            return serializers.TransactionClientRefundSerializer
        elif self.action == "credits_pay_all":
            return serializers.TransactionCreditPayAllSerializer
        elif self.action == "client_balance_transfer":
            return serializers.TransferClientBalanceSerializer
        elif self.action == "update_client_balance":
            return serializers.TransactionClientBalanceUpdateSerializer
        elif self.action == "medical_card_pay_all":
            return serializers.TransactionMedicalCardSerializer
        elif self.action == "medical_card_credit_all":
            return serializers.TransactionMedicalCardCreditSerializer
        return serializers.TransactionUpdateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_user"] = self.request.user
        return context

    @action(methods=["post"], url_name="credits_pay", detail=False)
    def credits_pay(self, request, *args, **kwargs):
        """
        Endpoint for creating transaction to pay for credit (partial/full)
        """
        return super().create(request, *args, **kwargs)

    @action(methods=["post"], url_name="clients_balance", detail=True)
    def clients_balance(self, request, *args, **kwargs):
        """
        Endpoint for updating client balance"
        """
        return super().create(request, *args, **kwargs)

    @action(methods=["patch"], url_name="update_client_balance", detail=True)
    def update_client_balance(self, request, **kwargs):
        return super().partial_update(request, **kwargs)

    @action(methods=["post"], url_name="clients_refund", detail=True)
    def clients_refund(self, request, *args, **kwargs):
        """
        Endpoint for refund of client balance
        """
        return super().create(request, *args, **kwargs)

    @action(methods=["post"], url_name="client_balance_transfer", detail=True)
    def client_balance_transfer(self, request, *args, **kwargs):
        """
        Endpoint for transferring client balance
        """
        return super().create(request, *args, **kwargs)

    @action(methods=["post"], url_name="credits_pay_all", detail=False)
    def credits_pay_all(self, request, *args, **kwargs):
        """
        Endpoint for repaying all unpaid credits of a client
        """
        return super().create(request, *args, **kwargs)

    @action(methods=["post"], url_name="medical_card_pay_all", detail=False)
    def medical_card_pay_all(self, request, *args, **kwargs):
        """
        Endpoint for repaying the whole medical card of client
        """
        return super().create(request, *args, **kwargs)

    @action(methods=["post"], url_name="medical_card_credit_all", detail=False)
    def medical_card_credit_all(self, request, *args, **kwargs):
        """
        Endpoint for crediting the whole medical card of clien
        """
        return super().create(request, *args, **kwargs)
