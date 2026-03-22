from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins, status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core.api.views import BaseViewSet
from apps.core.permissions import AccessPermissions
from apps.core.pagination import BasePagination

from apps.vacancies.api import serializers
from apps.vacancies import filtersets
from apps.vacancies.models import Vacancy, VacancyApplication


class VacancyViewSet(BaseViewSet):
    queryset = Vacancy.objects.annotate(
        applications_count=Count("applications")
    ).order_by("sort_order", "-created_at")
    serializer_class = serializers.VacancySerializer
    filterset_class = filtersets.VacancyFilterSet
    pagination_class = BasePagination
    permission_classes = (AccessPermissions,)


class VacancyApplicationViewSet(BaseViewSet):
    queryset = VacancyApplication.objects.select_related("vacancy").order_by("-created_at")
    serializer_class = serializers.VacancyApplicationAdminSerializer
    filterset_class = filtersets.VacancyApplicationFilterSet
    pagination_class = BasePagination
    permission_classes = (AccessPermissions,)


class VacancyPublicViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           BaseViewSet):
    queryset = Vacancy.objects.filter(is_active=True).order_by("sort_order", "-created_at")
    pagination_class = BasePagination
    permission_classes = (AllowAny,)
    http_method_names = ["get", "head", "options"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.VacancyPublicDetailSerializer
        return serializers.VacancyPublicListSerializer


class VacancyApplicationCreateView(CreateAPIView):
    queryset = VacancyApplication.objects.select_related("vacancy")
    serializer_class = serializers.VacancyApplicationSerializer
    permission_classes = (AllowAny,)
    parser_classes = [MultiPartParser, FormParser]


class VacancyApplicationStatusUpdateView(RetrieveAPIView):
    queryset = VacancyApplication.objects.select_related("vacancy")
    serializer_class = serializers.VacancyApplicationStatusSerializer
    permission_classes = (AccessPermissions,)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": _("Vacancy application status updated successfully."),
                "status": serializer.data["status"],
            },
            status=status.HTTP_200_OK,
        )
