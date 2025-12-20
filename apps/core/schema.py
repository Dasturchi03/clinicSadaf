import typing
from typing import List
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiExample
from apps.core.api.fields import SerializedPKRelatedField
from apps.core.api.serializers import WritableNestedSerializer
from rest_framework.relations import PrimaryKeyRelatedField, ManyRelatedField
from rest_framework.fields import IntegerField, DecimalField


WRITABLE_ACTIONS = ("PATCH", "POST", "PUT")
INTEGER_FIELDS = (IntegerField, DecimalField)


class CustomAutoSchema(AutoSchema):
    
    writable_serializers = {}
    
    def get_request_serializer(self) -> typing.Any:
        serializer = super().get_request_serializer()
        
        # handle mapping for Writable serializers - adapted from dansheps original code
        # for drf-yasg
        if serializer is not None and self.method in WRITABLE_ACTIONS:
            
            writable_class = self.get_writable_class(serializer)
            if writable_class is not None:
                if hasattr(serializer, "child"):
                    child_serializer = self.get_writable_class(serializer.child)
                    serializer = writable_class(context=serializer.context, child=child_serializer)
                else:
                    serializer = writable_class(context=serializer.context)
        return serializer
    
    def get_examples(self) -> List[OpenApiExample]:
        
        if hasattr(self.view, 'action') and self.view.action == 'bulk_create':
            serializer = self.get_request_serializer()
            modified_data = {}
            
            for field_name, field in serializer.fields.items():
                if isinstance(field, PrimaryKeyRelatedField) and not field.read_only:
                    modified_data[field_name] = 0
                if field_name not in modified_data.keys() and not field.read_only:
                    modified_data[field_name] = 0 if type(field) in INTEGER_FIELDS else 'string'
            
            example = OpenApiExample(
                name='Array of objects',
                value=[modified_data],
                media_type='application/json',
                status_codes=['200', '201']
            )
            return [example]
        return []
    
    def get_serializer_ref_name(self, serializer):
        # from drf-yasg.utils
        serializer_meta = getattr(serializer, 'Meta', None)
        serializer_name = type(serializer).__name__
        if hasattr(serializer_meta, 'ref_name'):
            ref_name = serializer_meta.ref_name
        elif serializer_name == 'NestedSerializer' and isinstance(serializer, serializers.ModelSerializer):
            ref_name = None
        else:
            ref_name = serializer_name
            if ref_name.endswith('Serializer'):
                ref_name = ref_name[: -len('Serializer')]
        return ref_name
    
    def get_writable_class(self, serializer):
        properties = {}
        fields = {} if hasattr(serializer, 'child') else serializer.fields
        remove_fields = []

        for child_name, child in fields.items():
            
            # read_only fields don't need to be in writable (write only) serializers
            if 'read_only' in dir(child) and child.read_only:
                remove_fields.append(child_name)
            if isinstance(child, (WritableNestedSerializer)):
                properties[child_name] = None
            elif isinstance(child, ManyRelatedField) and isinstance(child.child_relation, SerializedPKRelatedField):
                properties[child_name] = None

        if not properties:
            return None

        if type(serializer) not in self.writable_serializers:
            
            writable_name = 'Writable' + type(serializer).__name__
            meta_class = getattr(type(serializer), 'Meta', None)
            if meta_class:
                ref_name = 'Writable' + self.get_serializer_ref_name(serializer)
                # remove read_only fields from write-only serializers
                fields = list(meta_class.fields)
                for field in remove_fields:
                    fields.remove(field)
                writable_meta = type('Meta', (meta_class,), {'ref_name': ref_name, 'fields': fields})

                properties['Meta'] = writable_meta
            self.writable_serializers[type(serializer)] = type(writable_name, (type(serializer),), properties)

        writable_class = self.writable_serializers[type(serializer)]
        return writable_class
