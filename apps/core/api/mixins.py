from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response

from apps.core.exceptions import UniqueValidationError


class SequentialBulkCreatesMixin(CreateModelMixin):
    """
    Perform bulk creation of new objects sequentially, rather than all at once. This ensures that any validation
    which depends on the evaluation of existing objects (such as checking for free space within a rack) functions
    appropriately.
    """

    @action(methods=["POST"], detail=False)
    def bulk_create(self, request, *args, **kwargs):
        if not isinstance(request.data, list):
            # Creating a single object
            return super().create(request, *args, **kwargs)

        return_data = []
        for data in request.data:
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return_data.append(serializer.data)

        headers = self.get_success_headers(serializer.data)

        return Response(return_data, status=status.HTTP_201_CREATED, headers=headers)


class AutoUniqueValidatorMixin:
    """
    Mixin to automatically validate unique constraints (including those defined in the Meta class `constraints` option) for serializers.
    """

    def validate(self, attrs):
        ModelClass = self.Meta.model
        unique_constraints = ModelClass._meta.constraints
        include_nulls = getattr(ModelClass, "unique_constraints_include_nulls", False)

        errors = {"detail": [], "status_code": status.HTTP_400_BAD_REQUEST}
        error_message = _("Field with such value already exists: {}.")

        for constraint in unique_constraints:
            if isinstance(constraint, UniqueConstraint):
                fields = constraint.fields
                condition = constraint.condition
                filter_kwargs = {}

                missing_fields = False
                for field in fields:
                    if "restaurant" == field:
                        continue

                    if field in attrs:
                        value = attrs[field]
                    elif self.instance and hasattr(self.instance, field):
                        value = getattr(self.instance, field)
                    else:
                        # Missing field value, cannot perform uniqueness check
                        missing_fields = True
                        break

                    # Exclude fields with None value if include_nulls is False
                    if value is None and not include_nulls:
                        continue  # Skip this field
                    else:
                        filter_kwargs[field] = value

                if filter_kwargs.get("type") and len(filter_kwargs) == 1:
                    # Skip uniqueness check for static fields like type
                    # we can't define uniqueness with just one field
                    continue

                if missing_fields:
                    continue

                if not filter_kwargs:
                    continue

                if self.instance:
                    queryset = ModelClass.objects.exclude(pk=self.instance.pk)
                else:
                    queryset = ModelClass.objects.all()

                if condition:
                    queryset = queryset.filter(condition)

                if queryset.filter(**filter_kwargs).exists():
                    # Construct a human-readable field list for the error message
                    for field, value in filter_kwargs.items():
                        errors["detail"].append(
                            {"field_name": field, "error": error_message.format(value)}
                        )

        if errors["detail"]:
            raise UniqueValidationError(errors)

        return super().validate(attrs)
