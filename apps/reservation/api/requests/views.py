from drf_spectacular.utils import extend_schema
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.reservation import services
from apps.reservation.api.requests import serializers
from apps.reservation.models import ReservationRequest


@extend_schema(tags=["reservation_requests"])
class ReservationRequestViewSet(BaseViewSet):
    queryset = ReservationRequest.objects.select_related(
        "client", "doctor", "reservation", "reservation_work"
    )
    pagination_class = BasePagination

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return serializers.ReservationRequestDetailSerializer
        if self.action == "approve_by_clinic":
            return serializers.ReservationRequestApproveSerializer
        if self.action in [
            "cancell_by_clinic",
            "approve_by_patient",
            "cancell_by_patient",
        ]:
            return None
        return serializers.ReservationRequestSerializer

    @action(methods=["POST"], detail=True)
    def approve_by_clinic(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        valid_data = serializer.validated_data

        reservation_request = self.get_object()
        reservation_request = services.approve_reservation_request_by_clinic(
            reservation_request,
            end_time=valid_data["end_time"],
            is_initial=valid_data["is_initial"],
        )
        return Response(
            {
                "ok": True,
                "reservation_id": reservation_request.reservation.reservation_id,
                "status": reservation_request.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=["POST"], detail=True)
    def cancell_by_clinic(self, request, *args, **kwargs):
        reservation_request = self.get_object()
        reservation_request = services.cancel_reservation_request(
            reservation_request,
            cancelled_by_patient=False,
        )
        return Response(
            {"ok": True, "status": reservation_request.status},
            status=status.HTTP_200_OK,
        )

    @action(methods=["POST"], detail=True)
    def cancell_by_patient(self, request, *args, **kwargs):
        reservation_request = self.get_object()
        reservation_request = services.cancel_reservation_request(
            reservation_request,
            cancelled_by_patient=True,
        )
        return Response(
            {"ok": True, "detail": reservation_request.status},
            status=status.HTTP_200_OK,
        )

    @action(methods=["POST"], detail=True)
    def approve_by_patient(self, request, *args, **kwargs):
        reservation_request = self.get_object()
        reservation_request = services.approve_reservation_request_by_patient(
            reservation_request
        )
        return Response(
            {"ok": True, "detail": reservation_request.status},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["mobile_reservation"])
class MobileReservationRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = BasePagination

    def get_serializer_class(self):
        return serializers.MobileReservationRequestSerializer

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return ReservationRequest.objects.none()
        return ReservationRequest.objects.filter(client=client).select_related(
            "doctor", "reservation", "reservation_work"
        ).order_by("-created_at")


@extend_schema(tags=["mobile_reservation"])
class MobileReservationRequestDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileReservationRequestSerializer

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return ReservationRequest.objects.none()
        return ReservationRequest.objects.filter(client=client).select_related(
            "doctor", "reservation", "reservation_work"
        )


@extend_schema(tags=["mobile_reservation"])
class MobileReservationRequestCancelView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileReservationRequestSerializer
    http_method_names = ["patch"]

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return ReservationRequest.objects.none()
        return ReservationRequest.objects.filter(client=client).select_related(
            "doctor", "reservation", "reservation_work"
        )

    def patch(self, request, *args, **kwargs):
        reservation_request = services.cancel_reservation_request(
            self.get_object(),
            cancelled_by_patient=True,
        )
        serializer = self.get_serializer(reservation_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["mobile_reservation"])
class MobileReservationRequestConfirmView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileReservationRequestSerializer
    http_method_names = ["patch"]

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return ReservationRequest.objects.none()
        return ReservationRequest.objects.filter(client=client).select_related(
            "doctor", "reservation", "reservation_work"
        )

    def patch(self, request, *args, **kwargs):
        reservation_request = services.approve_reservation_request_by_patient(
            self.get_object()
        )
        serializer = self.get_serializer(reservation_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
