from rest_framework.relations import PrimaryKeyRelatedField, PKOnlyObject
from collections import OrderedDict


class SerializedPKRelatedField(PrimaryKeyRelatedField):
    """
    Extends PrimaryKeyRelatedField to return a serialized object on read. This is useful for representing related
    objects in a ManyToManyField while still allowing a set of primary keys to be written.
    """
    def __init__(self, serializer, **kwargs):
        self.serializer = serializer
        self.pk_field = kwargs.pop('pk_field', None)
        super().__init__(**kwargs)

    def to_representation(self, value, pk=False):
        if pk: return value.pk
        if isinstance(value, PKOnlyObject):
            value = self.queryset.get(pk=value.pk)
        data = self.serializer(value, context={'request': self.context['request']}).data
        return data
    
    def get_choices(self, cutoff=None):
        """
        This method is added to workaround a problem with hashable type. Source: https://github.com/encode/django-rest-framework/issues/5104
        """
        queryset = self.get_queryset()
        
        if queryset is None:
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([
            (
                self.to_representation(item, pk=True),
                self.display_value(item)
            )
            for item in queryset
        ])