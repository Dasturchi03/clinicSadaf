from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from apps.core.pagination import BasePagination
from apps.core.api.views import BaseViewSet
from apps.core.permissions import AccessPermissions

from apps.storage.api import serializers
from apps.storage import filtersets
from apps.storage.models import Storage, StorageItem, StorageHistory


class StorageItemViewSet(BaseViewSet):
    queryset = StorageItem.objects.filter(deleted=False).order_by("-item_id")
    filterset_class = filtersets.StorageItemFilterSet
    serializer_class = serializers.StorageItemSerializer
    pagination_class = BasePagination
    permission_classes = (AccessPermissions,)

    def get_serializer_context(self):
        context =  super().get_serializer_context()
        context["current_user"] = self.request.user
        return context

    def destroy(self, request, **kwargs):
        try:
            instance = self.get_object()
            if instance:
                storage = Storage.objects.filter(storage_item=instance, deleted=False)
                if storage.exists():
                    msg = "This item exists in a storage, delete storage instance first"
                    raise ValidationError(msg)
                data = {"Deleted successfully"}
                instance.deleted = True
                instance.save()
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {"Something went wrong!"}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except StorageItem.DoesNotExist:
            data = {"This type does not exist"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        

class StorageItemsListView(ListAPIView):
    """ Items that are not in storage"""
    serializer_class = serializers.StorageItemSerializer
    permission_classes = (AccessPermissions, )

    def get_queryset(self, **kwargs):
        storage_query = Storage.objects.all()
        return StorageItem.objects.filter(~Q(storage_item__in=storage_query), deleted=False)


class StorageViewSet(BaseViewSet):
    queryset = Storage.objects.filter(deleted=False).order_by("-storage_id")
    pagination_class = BasePagination
    filterset_class = filtersets.StorageFilterSet
    permission_classes = (AccessPermissions,)
    lookup_field = "storage_id"
    
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.StorageSerializer
        elif self.action == 'create':
            return serializers.StorageSerializer
        elif self.action == 'retrieve':
            return serializers.StorageSerializer
        elif self.action == "partial_update":
            return serializers.StorageSerializer
        elif self.action == "destroy":
            return serializers.StorageSerializer
        elif self.action == "add_quantity":
            return serializers.StorageSerializer
        elif self.action == "minus_quantity":
            return serializers.StorageSerializer
        elif self.action == "give_item":
            return serializers.StorageHistorySerializer

    def destroy(self, request, **kwargs):
        try:
            current_user = request.user
            instance = self.get_object()
            if instance:
                storage_history_instance = StorageHistory(
                    storage_history_type="delete",
                    storage_history_created_by=current_user,
                    storage_history_item=instance,
                    storage_history_item_measure=instance.storage_item_measure,
                    storage_history_item_quantity=instance.storage_quantity
                )
                storage_history_instance.save()
                data = {"Deleted successfully"}
                instance.deleted = True
                instance.save()
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {"Something went wrong!"}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except Storage.DoesNotExist:
            data = {"This type does not exist"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


    @action(methods=['patch'], url_name="add_quantity", detail=True, permission_classes=[])
    def add_quantity(self, request, **kwargs):
        """
        Add quantity for storage item
        """
        
        instance = self.get_object()
        current_user = request.user
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        storage_quantity = serializer.validated_data["storage_quantity"]

        storage_history_instance = StorageHistory(
            storage_history_type="add_quantity",
            storage_history_created_by=current_user,
            storage_history_item=instance,
            storage_history_item_measure=instance.storage_item_measure,
            storage_history_item_quantity=instance.storage_quantity+storage_quantity,
            storage_history_item_quantity_before=instance.storage_quantity,
        )
        storage_history_instance.save()
        instance.storage_quantity += storage_quantity
        instance.save(update_fields=["storage_quantity"])
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_name="minus_quantity", detail=True, permission_classes=[])
    def minus_quantity(self, request, **kwargs):
        """
        Minus quantity for storage item
        """
        
        instance = self.get_object()
        current_user = request.user
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        storage_quantity = serializer.validated_data["storage_quantity"]

        storage_history_instance = StorageHistory(
            storage_history_type="minus_quantity",
            storage_history_created_by=current_user,
            storage_history_item=instance,
            storage_history_item_measure=instance.storage_item_measure,
            storage_history_item_quantity=instance.storage_quantity - storage_quantity,
            storage_history_item_quantity_before=instance.storage_quantity,
        )
        storage_history_instance.save()
        instance.storage_quantity -= storage_quantity
        instance.save(update_fields=["storage_quantity"])
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_name="give_item", detail=True, permission_classes=[])
    def give_item(self, request, **kwargs):
        """
        Give item to the doctor
        """
        
        instance = self.get_object()
        current_user = request.user
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        storage_quantity = serializer.validated_data["storage_quantity"]
        doctor_instance = serializer.validated_data["storage_history_created_for"]

        storage_history_instance = StorageHistory(
            storage_history_type="give_item",
            storage_history_created_by=current_user,
            storage_history_created_for_id=doctor_instance["id"],
            storage_history_item=instance,
            storage_history_item_measure=instance.storage_item_measure,
            storage_history_item_quantity=storage_quantity,
            storage_history_item_quantity_before=instance.storage_quantity,
        )

        storage_history_instance.save()
        instance.storage_quantity -= storage_quantity
        instance.save(update_fields=["storage_quantity"])
        return Response(serializer.data, status=status.HTTP_200_OK)


class StorageHistoryViewSet(viewsets.ModelViewSet):
    queryset = StorageHistory.objects.order_by("-storage_history_id")
    serializer_class = serializers.StorageHistorySerializer
    filterset_class = filtersets.StorageHistoryFilter
    permission_classes = (AccessPermissions,)
    pagination_class = BasePagination
    http_method_names = ["get"]
