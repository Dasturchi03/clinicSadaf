from datetime import datetime

from django.db.models import Sum
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.response import Response

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.expenses import filtersets
from apps.expenses.api import serializers
from apps.expenses.models import ExpensesType, FinancialReport, IncomeType


class ExpensesTypeViewSet(BaseViewSet):
    queryset = ExpensesType.objects.order_by("-expenses_type_id")
    pagination_class = BasePagination
    serializer_class = serializers.ExpensesTypeSerializer
    filterset_class = filtersets.ExpensesTypeFilter
    permission_classes = (AccessPermissions,)


class ExpensesChildListView(generics.ListAPIView):
    serializer_class = serializers.ExpensesTypeSerializer
    permission_classes = (AccessPermissions,)

    def get_queryset(self, **kwargs):
        return ExpensesType.objects.filter(type_parent_id=self.kwargs.get("pk"))


class IncomeTypeViewSet(BaseViewSet):
    queryset = IncomeType.objects.order_by("-id")
    pagination_class = BasePagination
    serializer_class = serializers.IncomeTypeSerializer
    filterset_class = filtersets.IncomeTypeFilter
    permission_classes = (AccessPermissions,)


class IncomeTypeChildListView(generics.ListAPIView):
    serializer_class = serializers.IncomeTypeSerializer
    permission_classes = (AccessPermissions,)

    def get_queryset(self, **kwargs):
        return IncomeType.objects.filter(parent=self.kwargs.get("pk"))


class FinancialReportViewSet(BaseViewSet):
    queryset = FinancialReport.objects.select_related(
        "report_for_user",
        "report_for_client",
        "report_expense_type",
        "report_income_type",
        "report_storage_item",
    ).order_by("-report_id")
    pagination_class = BasePagination
    filterset_class = filtersets.FinancialReportFilter
    permission_classes = (AccessPermissions,)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.FinancialReportListSerializer
        elif self.action in ["create", "retrieve"]:
            return serializers.FinancialReportSerializer
        return serializers.FinancialReportUpdateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_user"] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if instance:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"ok": True}, status=status.HTTP_201_CREATED)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="start_date",
            required=True,
            type=OpenApiTypes.DATE,
        ),
        OpenApiParameter(
            name="end_date",
            required=True,
            type=OpenApiTypes.DATE,
        ),
    ],
)
class FinancialReportIncomeTotalsView(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = serializers.FinancialReportTotalsSerializer
    filterset_class = filtersets.FinancialReportFilter

    def get_queryset(self):
        queryset = FinancialReport.objects.filter(
            report_income_type__isnull=False,
        )
        if self.request.query_params:
            return super().filter_queryset(queryset)
        return queryset

    def list(self, request, *args, **kwargs):
        # Parse start and end dates from the request parameters
        start_date = datetime.strptime(
            request.query_params.get("start_date"), "%d-%m-%Y"
        ).date()
        end_date = datetime.strptime(
            request.query_params.get("end_date"), "%d-%m-%Y"
        ).date()

        total_sum = (
            self.get_queryset()
            .filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .aggregate(total_sum=Sum("report_sum"))["total_sum"]
            or 0
        )
        return Response({"total_sum": total_sum}, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="start_date",
            required=True,
            type=OpenApiTypes.DATE,
        ),
        OpenApiParameter(
            name="end_date",
            required=True,
            type=OpenApiTypes.DATE,
        ),
    ],
)
class FinancialReportExpenseTotalsView(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = serializers.FinancialReportTotalsSerializer
    filterset_class = filtersets.FinancialReportFilter

    def get_queryset(self):
        queryset = FinancialReport.objects.filter(
            report_expense_type__isnull=False,
        )
        if self.request.query_params:
            return super().filter_queryset(queryset)
        return queryset

    def list(self, request, *args, **kwargs):
        # Parse start and end dates from the request parameters
        start_date = datetime.strptime(
            request.query_params.get("start_date"), "%d-%m-%Y"
        ).date()
        end_date = datetime.strptime(
            request.query_params.get("end_date"), "%d-%m-%Y"
        ).date()

        total_sum = (
            self.get_queryset()
            .filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .aggregate(total_sum=Sum("report_sum"))["total_sum"]
            or 0
        )
        return Response({"total_sum": total_sum}, status=status.HTTP_200_OK)
