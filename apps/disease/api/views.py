from rest_framework.generics import ListAPIView

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions

from apps.disease.models import Disease
from apps.disease.api import serializers
from apps.disease import filtersets


class DiseaseViewSet(BaseViewSet):
    queryset = Disease.objects.select_related("parent").prefetch_related("disease_child", "work_disease").exclude(disease_title="Архив")
    pagination_class = BasePagination
    filterset_class = filtersets.DiseaseFilter
    permission_classes = (AccessPermissions, )

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.DiseaseSerializer
        if self.action == "list":
            return serializers.DiseaseListSerializer
        if self.action == "retrieve":
            return serializers.DiseaseSerializer
        if self.action == "partial_update":
            return serializers.DiseaseSerializer


class DiseaseChildListView(ListAPIView):
    serializer_class = serializers.DiseaseListSerializer
    permission_classes = (AccessPermissions, )

    def get_queryset(self, **kwargs):
        return Disease.objects.filter(parent_id=self.kwargs.get("pk"))


class DiseaseChildAllListView(ListAPIView):
    serializer_class = serializers.DiseaseListSerializer
    permission_classes = (AccessPermissions,)

    def get_queryset(self, **kwargs):
        return Disease.objects.filter(parent_isnull=False)