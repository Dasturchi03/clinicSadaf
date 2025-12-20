from rest_framework import status
from rest_framework.response import Response

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.work import filtersets
from apps.work.api import serializers
from apps.work.models import Work


class WorkViewSet(BaseViewSet):
    queryset = (
        Work.objects.filter(deleted=False)
        .prefetch_related(
            "category", "disease", "specialization", "print_out_categories"
        )
        .order_by("-work_id")
    )
    serializer_class = serializers.WorkSerializer
    filterset_class = filtersets.WorkFilterSet
    permission_classes = (AccessPermissions,)
    pagination_class = BasePagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_user"] = self.request.user
        return context

    def destroy(self, request, **kwargs):
        instance = self.get_object()
        instance.deleted = True
        instance.save(update_fields=["deleted"])
        return Response({"Удаление успешно!"}, status=status.HTTP_200_OK)
