from rest_framework import serializers
from django.db.models import ManyToManyField
from django.core.exceptions import FieldError, MultipleObjectsReturned, ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from rest_framework.utils import model_meta


class BaseModelSerializer(serializers.ModelSerializer):
    
    def update(self, instance, validated_data):
        info = model_meta.get_field_info(instance)
        
        m2m_fields = []
        update_fields = []
        
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)
                update_fields.append(attr)
                
        instance.save(update_fields=update_fields)

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)
        return instance
        
        
class ValidatedModelSerializer(serializers.ModelSerializer):
    def validate(self, data):

        # Remove custom fields data and tags (if any) prior to model validation
        attrs = data.copy()
        
        # Skip ManyToManyFields
        for field in self.Meta.model._meta.get_fields():
            if isinstance(field, ManyToManyField):
                attrs.pop(field.name, None)

        # Run clean() on an instance of the model
        if self.instance is None:
            instance = self.Meta.model(**attrs)
        else:
            instance = self.instance
            for k, v in attrs.items():
                setattr(instance, k, v)
    
        instance.full_clean()
        return data
    
    
class WritableNestedSerializer(serializers.ModelSerializer):

    def to_internal_value(self, data):

        if data is None:
            return None

        # Dictionary of related object attributes
        if isinstance(data, dict):
            queryset = self.Meta.model.objects
            try:
                return queryset.get(**data)
            except ObjectDoesNotExist:
                raise ValidationError(f"Related object not found using the provided attributes: {data}")
            except MultipleObjectsReturned:
                raise ValidationError(f"Multiple objects match the provided attributes: {data}")
            except FieldError as e:
                raise ValidationError(e)

        # Integer PK of related object
        try:
            # Cast as integer in case a PK was mistakenly sent as a string
            pk = int(data)
        except (TypeError, ValueError):
            raise ValidationError(
                f"Related objects must be referenced by numeric ID or by dictionary of attributes. Received an "
                f"unrecognized value: {data}"
            )

        # Look up object by PK
        try:
            return self.Meta.model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(f"Related object not found using the provided numeric ID: {pk}")
        
        
class ImageModelSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data['image_thumbnail'] = validated_data['image']
        validated_data['image_medium'] = validated_data['image']
        image = super().create(validated_data)
        return image


class EmptySerializer(serializers.Serializer):
    pass