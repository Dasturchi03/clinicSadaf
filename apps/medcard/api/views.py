from django.db.models import Prefetch
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.medcard import filtersets
from apps.medcard.api import serializers
from apps.medcard.models import Action, MedicalCard, Stage, Tooth, Xray


@extend_schema(tags=["medical_card"])
class MedicalCardListView(BaseViewSet):
    queryset = MedicalCard.objects.all()
    serializer_class = serializers.MedicalCardListSerializer
    filterset_class = filtersets.MedicalCardFilter
    permission_classes = (AccessPermissions,)


@extend_schema(tags=["tooth"])
class ToothListView(ListAPIView):
    """To get list of adult teeth use 'Adult' parameter, to get list of child teeth use 'Child' parameter"""

    queryset = Tooth.objects.all().order_by("tooth_id")
    serializer_class = serializers.ToothSerializer
    filterset_fields = ("tooth_type",)
    permission_classes = (AccessPermissions,)


@extend_schema(tags=["medical_card"])
class ActionViewset(BaseViewSet):
    queryset = Action.objects.all()
    permission_classes = (AccessPermissions,)
    serializer_class = serializers.ActionViewSetUpdateSerializer
    http_method_names = ["put", "patch", "delete", "get"]

    def perform_destroy(self, instance):
        medcard = instance.action_stage.card
        instance.delete()
        stage_query = Stage.objects.select_related("card").filter(card_id=medcard.pk)
        action_query = Action.objects.filter(action_stage__in=stage_query)
        actions_sum = sum(action.action_price for action in action_query)

        medcard.card_price = actions_sum if actions_sum else 0
        medcard.save()
        return medcard


@extend_schema(tags=["medical_card"])
class MedicalCardViewSet(BaseViewSet):
    pagination_class = BasePagination
    permission_classes = (AccessPermissions,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_user"] = self.request.user
        return context

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.MedicalCardListSerializer
        if self.action == "create":
            return serializers.MedicalCardCreateSerializer
        if self.action == "retrieve":
            return serializers.MedicalCardCreateSerializer
        if self.action == "partial_update":
            return serializers.MedicalCardUpdateSerializer

    def get_queryset(self, *args, **kwargs):
        queryset = MedicalCard.objects.filter(client_id=self.kwargs.get("client_id"))
        return queryset.order_by("-card_id")

    def get_object(self):
        instance = (
            MedicalCard.objects.filter(pk=self.kwargs.get("pk"))
            .select_related("client")
            .prefetch_related(
                Prefetch(
                    lookup="stage",
                    queryset=Stage.objects.select_related("stage_created_by", "tooth")
                    .prefetch_related(
                        Prefetch(
                            lookup="action_stage",
                            queryset=Action.objects.select_related(
                                "action_created_by",
                                "action_doctor",
                                "action_work",
                                "action_disease",
                            ).prefetch_related("transaction_action", "credit_action"),
                        )
                    )
                    .order_by("tooth__tooth_id"),
                )
            )
            .first()
        )
        if instance:
            return instance
        else:
            raise Http404


@extend_schema(tags=["x_ray"])
class XrayViewSet(BaseViewSet):
    queryset = Xray.objects.select_related("client", "tooth").order_by("-created_at")
    filterset_class = filtersets.XrayFilter
    pagination_class = BasePagination

    def get_serializer_class(self):
        if self.action == "bulk_upload":
            return serializers.XrayBulkUploadSerializer
        if self.action in ["list", "retrieve"]:
            return serializers.XrayDetailSerializer
        return serializers.XraySerializer

    @action(methods=["POST"], detail=False)
    def bulk_upload(self, request, *args, **kwargs):
        client = request.data.get("client")
        medical_card = request.data.get("medical_card", None)
        stage = request.data.get("stage", None)
        tooth = request.data.get("tooth", None)
        images = request.FILES.getlist("images")

        for image in images:
            xray_data = {
                "client": client,
                "medical_card": medical_card,
                "stage": stage,
                "tooth": tooth,
                "image": image,
            }
            serializer = serializers.XraySerializer(data=xray_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response({"ok": True}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["mobile_reservation"],
    parameters=[
        OpenApiParameter(
            name="status",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filter treatments by status: active, in_progress, paid.",
        ),
    ],
)
class MobileTreatmentListView(ListAPIView):
    serializer_class = serializers.MobileTreatmentListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = BasePagination

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return MedicalCard.objects.none()
        queryset = (
            MedicalCard.objects.filter(client=client)
            .prefetch_related("transaction_card", "credit_card")
            .order_by("-card_created_at")
        )
        status_filter = self.request.query_params.get("status")
        if status_filter == "paid":
            queryset = queryset.filter(card_is_paid=True)
        elif status_filter == "in_progress":
            queryset = queryset.filter(card_is_paid=False, card_is_done=True)
        elif status_filter == "active":
            queryset = queryset.filter(card_is_paid=False)
        return queryset


@extend_schema(tags=["mobile_reservation"])
class MobileTreatmentDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.MobileTreatmentDetailSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return MedicalCard.objects.none()
        return (
            MedicalCard.objects.filter(client=client)
            .select_related("client")
            .prefetch_related(
                "transaction_card",
                "credit_card",
                Prefetch(
                    "stage",
                    queryset=Stage.objects.select_related("tooth").prefetch_related(
                        Prefetch(
                            "action_stage",
                            queryset=Action.objects.select_related(
                                "action_doctor", "action_work"
                            ).order_by("action_id"),
                        )
                    ).order_by("stage_index"),
                ),
            )
        )
