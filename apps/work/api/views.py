from drf_spectacular.utils import OpenApiParameter, extend_schema
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import AllowAny
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


@extend_schema(
    tags=["mobile_content"],
    parameters=[
        OpenApiParameter(
            name="doctor_id",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filter services available for a specific doctor.",
        ),
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filter by category title or category id.",
        ),
        OpenApiParameter(
            name="q",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Search by service title.",
        ),
    ],
)
class MobileWorkListView(generics.ListAPIView):
    serializer_class = serializers.MobileWorkSerializer
    permission_classes = (AllowAny,)
    pagination_class = BasePagination

    def get_queryset(self):
        queryset = (
            Work.objects.filter(deleted=False)
            .prefetch_related("category", "specialization")
            .order_by("work_title")
        )
        doctor_id = self.request.query_params.get("doctor_id")
        category = self.request.query_params.get("category")
        q = self.request.query_params.get("q")

        if doctor_id:
            queryset = queryset.filter(
                Q(specialization__user_specialization__id=doctor_id)
                | Q(specialization__isnull=True)
            )
        if category:
            category_query = Q(category__category_title__icontains=category)
            if category.isdigit():
                category_query |= Q(category__category_id=int(category))
            queryset = queryset.filter(category_query)
        if q:
            queryset = queryset.filter(work_title__icontains=q)
        return queryset.distinct()


@extend_schema(tags=["mobile_content"])
class MobileWorkDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.MobileWorkSerializer
    permission_classes = (AllowAny,)
    queryset = Work.objects.filter(deleted=False).prefetch_related(
        "category", "specialization"
    )
