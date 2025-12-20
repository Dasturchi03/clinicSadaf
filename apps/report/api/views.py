from apps.core.pagination import BasePagination
from apps.core.api.views import BaseViewSet
from apps.core.permissions import AccessPermissions

from apps.report import filtersets
from apps.report.api import serializers
from apps.report.models import MedicalCardReport


class MedicalCardReportViewSet(BaseViewSet):
    queryset = MedicalCardReport.objects.select_related(
        "client", "doctor", "action"
    ).prefetch_related(
        "credits", "financial_reports", "transactions", "salaries"
    ).order_by("-created_at")
    pagination_class = BasePagination
    filterset_class = filtersets.MedicalCardReportFilter
    permission_classes = (AccessPermissions,)
    http_method_names = ["get"]
    
    def get_serializer_class(self):
        if self.action == "list":
            return serializers.MedicalCardReportListSerializer
        return serializers.MedicalCardReportDetailSerializer