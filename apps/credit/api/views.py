from apps.credit.models import Credit
from apps.credit.api import serializers

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions



class CreditViewSet(BaseViewSet):
    pagination_class = BasePagination
    permission_classes = (AccessPermissions, )
    http_method_names = ["get", "delete", "patch", "put"]

    def get_serializer_class(self):
        if self.action in ["list", "get"]:
            return serializers.CreditSerializer
        return serializers.CreditUpdateSerializer

    def get_queryset(self):
        queryset = Credit.objects.filter(credit_client_id=self.kwargs.get("client_id"))
        return self.filter_queryset(queryset).order_by("-credit_id")

    def get_object(self):
        instance = Credit.objects.get(pk=self.kwargs.get("credit_id"))
        return instance