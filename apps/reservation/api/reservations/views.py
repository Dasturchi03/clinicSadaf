from datetime import date

from django.db.models import Prefetch
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.user.models import User
from apps.client.models import Client_Public_Phone
from apps.core.api.serializers import EmptySerializer
from apps.core.api.views import BaseViewSet
from apps.core.choices import ReservationRequestStatuses
from apps.core.permissions import AccessPermissions
from apps.reservation import filtersets
from apps.reservation.api.reservations import serializers
from apps.reservation.filtersets import ReservationDoctorsFilter
from apps.reservation.models import Reservation


@extend_schema(tags=["reservations"])
class ReservationViewSet(BaseViewSet):
    queryset = Reservation.objects.all()
    permission_classes = (AccessPermissions,)
    lookup_field = "reservation_id"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.ReservationSerializer
        elif self.action == "partial_update":
            return serializers.ReservationUpdateSerializer
        elif self.action == "create":
            return serializers.ReservationSerializer
        elif self.action == "force_update":
            return serializers.ReservationForceUpdateSerializer
        elif self.action == "cancel":
            return EmptySerializer

    @action(
        methods=["patch"], url_name="force_update", detail=False, permission_classes=[]
    )
    def force_update(self, request, **kwargs):
        instance = self.get_object()
        current_user = request.user
        serializer = self.get_serializer(
            instance, data=request.data, context={"current_user": current_user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["put"], url_name="cancel", detail=False, permission_classes=[])
    def cancel(self, request, *args, **kwargs):
        current_user = request.user
        try:
            instance = self.get_object()
            doctor_instance = instance.reservation_doctor

            if (
                current_user.user_type.type_text == "Доктор"
                and doctor_instance.pk != current_user.pk
            ):
                raise ValidationError(
                    "Врач может отменить только свою запись, обратитесь в регистратуру"
                )
            instance.cancelled = True
            instance.save()
            if (
                hasattr(instance, "reservation_request")
                and instance.reservation_request
            ):
                instance.reservation_request.status = (
                    ReservationRequestStatuses.CANCELLED
                )
                instance.reservation_request.save()
            data = {"Cancelled successfully"}
            return Response(data, status=status.HTTP_200_OK)
        except Reservation.DoesNotExist:
            data = {"Reservation has already been cancelled"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        instance = self.get_object()
        current_user = request.user
        doctor_instance = instance.reservation_doctor
        if (
            current_user.user_type.type_text == "Доктор"
            and doctor_instance.pk != current_user.pk
        ):
            raise ValidationError(
                "Врач может удалить только свою запись, обратитесь в регистратуру"
            )

        self.perform_destroy(instance=instance)
        return Response({"Удаление успешно!"}, status=status.HTTP_200_OK)


class ReservationListView(generics.ListAPIView):
    filterset_class = filtersets.ReservationFilter
    serializer_class = serializers.ReservationListSerializer
    permission_classes = (AccessPermissions,)

    def get_queryset(self):
        queryset = (
            Reservation.objects.filter(reservation_date=date.today())
            .select_related("reservation_client", "reservation_work")
            .prefetch_related(
                Prefetch(
                    lookup="reservation_client__client_public_phone",
                    queryset=Client_Public_Phone.objects.only(
                        "client_id", "public_phone"
                    ),
                )
            )
            .only(
                "reservation_id",
                "reservation_doctor_id",
                "reservation_notes",
                "reservation_date",
                "reservation_start_time",
                "reservation_doctor_id",
                "reservation_end_time",
                "cancelled",
                "created_at",
                "reservation_client__client_id",
                "reservation_client__client_firstname",
                "reservation_client__client_lastname",
                "reservation_client__client_birthdate",
                "reservation_work__work_id",
                "reservation_work__work_title",
                "reservation_work__work_title_en",
                "reservation_work__work_title_ru",
                "reservation_work__work_title_uz",
                "reservation_work__work_basic_price",
            )
        )

        if self.request.query_params:
            queryset = (
                Reservation.objects.select_related(
                    "reservation_client", "reservation_work"
                )
                .prefetch_related(
                    Prefetch(
                        lookup="reservation_client__client_public_phone",
                        queryset=Client_Public_Phone.objects.only(
                            "client_id", "public_phone"
                        ),
                    )
                )
                .only(
                    "reservation_id",
                    "reservation_doctor_id",
                    "reservation_notes",
                    "reservation_date",
                    "reservation_start_time",
                    "reservation_doctor_id",
                    "reservation_end_time",
                    "cancelled",
                    "created_at",
                    "reservation_client__client_id",
                    "reservation_client__client_firstname",
                    "reservation_client__client_lastname",
                    "reservation_client__client_birthdate",
                    "reservation_work__work_id",
                    "reservation_work__work_title",
                    "reservation_work__work_title_en",
                    "reservation_work__work_title_ru",
                    "reservation_work__work_title_uz",
                    "reservation_work__work_basic_price",
                )
            )
            return super().filter_queryset(queryset)

        return queryset


class ReservationDoctorsView(generics.RetrieveAPIView, generics.ListAPIView):
    filterset_class = ReservationDoctorsFilter

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.kwargs.get('pk', None):
            return serializers.ReservationDoctorDetailSerializer
        return serializers.ReservationDoctorsSerializer

    def get_queryset(self):
        return (
            User.objects
            .select_related("user_type")
            .prefetch_related("user_specialization", "user_schedule", "reservations")
            .only("id", "user_firstname", "user_lastname", "user_image", "user_type__user_type_id", "user_type__type_text")
            .filter(user_type__type_text='Доктор')
        )


def index(request, username):
    return render(request, "reservation/index.html", context={"username": username})
