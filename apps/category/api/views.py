from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated

from apps.category import filtersets
from apps.category.api import serializers
from apps.category.models import Category, PrintOutCategory
from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.work.models import Work


class CategoryViewSet(BaseViewSet):
    queryset = (
        Category.objects.prefetch_related("work_category")
        .order_by("-category_id")
        .exclude(category_title="Архив")
    )
    serializer_class = serializers.CategorySerializer
    filterset_class = filtersets.CategoryFilterSet
    permission_classes = (AccessPermissions,)
    pagination_class = BasePagination

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]


class PrintOutCategoryViewSet(BaseViewSet):
    queryset = PrintOutCategory.objects.prefetch_related(
        Prefetch(lookup="works", queryset=Work.objects.only("work_id", "work_title"))
    ).order_by("order_index")
    filterset_class = filtersets.PrintOutCategoryFilterSet
    permission_classes = (AccessPermissions,)
    pagination_class = BasePagination

    def get_serializer_class(self):
        if self.action in ["list", "create"]:
            return serializers.PrintOutCategorySerializer
        return serializers.PrintOutCategoryDetailSerializer
