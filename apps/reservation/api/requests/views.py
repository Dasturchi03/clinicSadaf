from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.api.views import BaseViewSet
from apps.core.choices import ReservationRequestStatuses
from apps.core.pagination import BasePagination
from apps.notifications.models import Notification
from apps.reservation import services
from apps.reservation import filtersets
from apps.reservation.api.requests import serializers
from apps.reservation.models import Reservation, ReservationRequest


@extend_schema(tags=["reservation_requests"])
class ReservationRequestViewSet(BaseViewSet):
    queryset = ReservationRequest.objects.all()
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
        services.ensure_reservation_available(
            doctor=reservation_request.doctor,
            target_date=reservation_request.date,
            start_time=reservation_request.time,
            end_time=valid_data["end_time"],
        )
        reservation_instance = Reservation.objects.create(
            reservation_client=reservation_request.client,
            reservation_doctor=reservation_request.doctor,
            reservation_work=reservation_request.reservation_work,
            reservation_notes=reservation_request.note,
            reservation_date=reservation_request.date,
            reservation_start_time=reservation_request.time,
            reservation_end_time=valid_data["end_time"],
            is_initial=valid_data["is_initial"],
        )
        Notification.objects.create(
            notification_reservation=reservation_instance,
            notification_receiver=reservation_request.doctor,
            notification_message="",
        )
        reservation_request.reservation = reservation_instance
        reservation_request.status = ReservationRequestStatuses.APPROVED
        reservation_request.save()
        return Response(
            {
                "ok": True,
                "reservation_id": reservation_instance.reservation_id,
                "status": ReservationRequestStatuses.APPROVED,
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=["POST"], detail=True)
    def cancell_by_clinic(self, request, *args, **kwargs):
        reservation_request = self.get_object()
        reservation_request.status = ReservationRequestStatuses.CANCELLED
        reservation_request.save()
        if (
            hasattr(reservation_request, "reservation")
            and reservation_request.reservation
        ):
            reservation_request.reservation.cancelled = True
            reservation_request.reservation.save()
        return Response(
            {"ok": True, "status": ReservationRequestStatuses.CANCELLED},
            status=status.HTTP_200_OK,
        )

    @action(methods=["POST"], detail=True)
    def cancell_by_patient(self, request, *args, **kwargs):
        reservation_request = self.queryset.filter(
            flutter_reservation_id=self.kwargs.get("pk")
        ).first()
        if not reservation_request:
            return Response(
                {
                    "ok": False,
                    "detail": f"Reservation request with id: {self.kwargs.get('pk')} does not exists",
                }
            )

        reservation_request.status = ReservationRequestStatuses.CANCELLED_BY_PATIENT
        reservation_request.save()
        if (
            hasattr(reservation_request, "reservation")
            and reservation_request.reservation
        ):
            reservation_request.reservation.cancelled = True
            reservation_request.reservation.cancelled_by_patient = True
            reservation_request.reservation.save()
        return Response(
            {"ok": True, "detail": ReservationRequestStatuses.CANCELLED_BY_PATIENT},
            status=status.HTTP_200_OK,
        )

    @action(methods=["POST"], detail=True)
    def approve_by_patient(self, request, *args, **kwargs):
        reservation_request = self.queryset.filter(
            flutter_reservation_id=self.kwargs.get("pk")
        ).first()
        if not reservation_request:
            return Response(
                {
                    "ok": False,
                    "detail": f"Reservation request with id: {self.kwargs.get('pk')} does not exists",
                }
            )

        reservation_request.status = ReservationRequestStatuses.APPROVED_BY_PATIENT
        reservation_request.save()
        return Response(
            {"ok": True, "detail": ReservationRequestStatuses.APPROVED_BY_PATIENT},
            status=status.HTTP_200_OK,
        )

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
            "doctor", "reservation"
        ).order_by("-created_at")


class MobileReservationRequestDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileReservationRequestSerializer

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return ReservationRequest.objects.none()
        return ReservationRequest.objects.filter(client=client).select_related(
            "doctor", "reservation"
        )


class MobileReservationRequestCancelView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MobileReservationRequestSerializer
    http_method_names = ["patch"]

    def get_queryset(self):
        client = getattr(self.request.user, "client_user", None)
        if not client:
            return ReservationRequest.objects.none()
        return ReservationRequest.objects.filter(client=client).select_related(
            "reservation"
        )

    def patch(self, request, *args, **kwargs):
        reservation_request = self.get_object()
        reservation_request.status = ReservationRequestStatuses.CANCELLED_BY_PATIENT
        reservation_request.save(update_fields=["status"])
        if reservation_request.reservation:
            reservation_request.reservation.cancelled = True
            reservation_request.reservation.cancelled_by_patient = True
            reservation_request.reservation.save(
                update_fields=["cancelled", "cancelled_by_patient"]
            )
        serializer = self.get_serializer(reservation_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
