from rest_framework.permissions import BasePermission, DjangoObjectPermissions


class ObjectPermission(DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_object_permission(self, request, view, obj):
        # authentication checks have already executed via has_permission
        queryset = self._queryset(view)
        model_cls = queryset.model
        user = request.user

        perms = self.get_required_object_permissions(request.method, model_cls)


class UserPermissions(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.has_perm('user.view_user_permissions'):
            return True
        else:
            return False

