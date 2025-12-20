from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.user.api.serializers import DoctorSerializer
from apps.storage.models import Storage, StorageItem, StorageHistory


class ItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(required=False)

    class Meta:
        model = StorageItem
        fields = [
            "item_id",
            "item_name",
            "item_measure",
            "created_at",
        ]
        extra_kwargs = {
            "item_name": {"read_only": True},
            "item_measure": {"read_only": True},
            "created_at": {"read_only": True},
        }


class StorageItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = StorageItem
        fields = [
            "item_id",
            "item_name",
            "item_measure",
            "deleted",
            "created_at"
        ]
        extra_kwargs = {
            "item_id": {"read_only": True},
            "deleted": {"read_only": True},
            "created_at": {"read_only": True},
        }

    def create(self, validated_data):
        item = StorageItem.objects.filter(item_name__iexact=validated_data.get("item_name"), deleted=False)
        if item.exists():
            msg = "Storage item with that name already exists"
            raise ValidationError(msg)
        current_user = self.context.get("current_user")
        item_instance = StorageItem(item_created_by=current_user,
                                    item_name=validated_data.get("item_name"),
                                    item_measure=validated_data.get("item_measure"))
        item_instance.save()
        return item_instance

    def update(self, instance, validated_data):
        item = StorageItem.objects.filter(item_name__iexact=validated_data.get("item_name"), deleted=False)
        if item.exists():
            msg = "Storage item with that name already exists"
            raise ValidationError(msg)
        instance.item_name = validated_data.get("item_name", instance.item_name)
        instance.item_measure = validated_data.get("item_measure", instance.item_measure)
        Storage.objects.filter(storage_item=instance, deleted=False).update(storage_item_measure=instance.item_measure)
        instance.save()
        return instance


class StorageSerializer(serializers.ModelSerializer):
    storage_item = ItemSerializer(required=False)

    class Meta:
        model = Storage
        fields = [
            "storage_id",
            "storage_item",
            "storage_item_measure",
            "storage_quantity",
            "created_at"
        ]
        extra_kwargs = {
            "storage_item_measure": {"read_only": True}
        }

    def create(self, validated_data):
        current_user = self.context.get("current_user")

        storage_item = validated_data.pop("storage_item")

        item_instance = StorageItem.objects.get(pk=storage_item.get("item_id"), deleted=False)
        storage_instance = Storage.objects.filter(storage_item=item_instance, deleted=False)
        if not storage_instance.exists():
            storage_instance = Storage(
                storage_created_by=current_user,
                storage_item=item_instance,
                storage_item_measure=item_instance.item_measure,
                storage_quantity=validated_data.get("storage_quantity")
            )
            storage_instance.save()
            return storage_instance

        else:
            msg = "Item already exists in a storage"
            raise ValidationError(msg)

    def update(self, instance, validated_data):
        current_user = self.context.get("current_user")

        storage_item = validated_data.pop("storage_item", None)
        if storage_item:
            item_instance = StorageItem.objects.get(pk=storage_item.get("item_id"), deleted=False)
            storage_instance = Storage.objects.filter(storage_item=item_instance, deleted=False)

            if storage_instance.exists():
                msg = "Item already exists in a storage"
                raise ValidationError(msg)

            instance.storage_item = item_instance
            instance.storage_item_measure = item_instance.item_measure

        storage_quantity = validated_data.get("storage_quantity", None)
        if storage_quantity:
            storage_history_instance = StorageHistory(
                storage_history_created_by=current_user,
                storage_history_item=instance,
                storage_history_item_measure=instance.storage_item_measure,
                storage_history_item_quantity=storage_quantity,
                storage_history_item_quantity_before=instance.storage_quantity,
            )

            instance.storage_quantity = storage_quantity
            storage_history_instance.save()

        instance.save()
        return instance


class ItemHistorySerializer(serializers.ModelSerializer):
    storage_item = ItemSerializer(required=False)

    class Meta:
        model = Storage
        fields = [
            "storage_id",
            "storage_item"
        ]
        extra_kwargs = {
            "storage_item_measure": {"read_only": True}
        }


class StorageHistorySerializer(serializers.ModelSerializer):
    storage_history_created_for = DoctorSerializer(required=False)
    storage_history_item = serializers.SerializerMethodField("get_storage_history_item")
    storage_quantity = serializers.FloatField(write_only=True)

    class Meta:
        model = StorageHistory
        fields = [
            "storage_history_id",
            "storage_history_type",
            "storage_history_created_for",
            "storage_quantity",
            "storage_history_item",
            "storage_history_item_measure",
            "storage_history_item_quantity",
            "storage_history_item_quantity_before",
            "created_at"
        ]
        extra_kwargs = {
            "storage_history_item_measure": {"read_only": True},
            "storage_history_item_quantity": {"read_only": True},
            "storage_history_item_quantity_before": {"read_only": True},
        }

    def get_storage_history_item(self, obj):
        serializer = ItemHistorySerializer(obj.storage_history_item)
        return serializer.data
