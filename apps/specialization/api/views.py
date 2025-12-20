from apps.core.api.views import BaseViewSet
from apps.core.permissions import AccessPermissions
from apps.core.pagination import BasePagination

from apps.specialization.api import serializers
from apps.specialization import filtersets
from apps.specialization.models import Specialization


class SpecializationViewSet(BaseViewSet):
    queryset = Specialization.objects.prefetch_related("work_specialization", "user_specialization").order_by("-specialization_id").exclude(specialization_text="Архив")
    serializer_class = serializers.SpecializationSerializer
    filterset_class = filtersets.SpecializationFilterSet
    pagination_class = BasePagination
    permission_classes = (AccessPermissions,)