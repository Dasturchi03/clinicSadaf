from rest_framework.permissions import DjangoModelPermissions


class AccessPermissions(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_permission(self, request, view):
        if getattr(view, '_ignore_model_permissions', False):
            return True
        if not request.user or (
                not request.user.is_authenticated and self.authenticated_users_only):
            return False
        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)
        user = request.user
        if user.is_superuser:
            return True
        if user.has_perms(perms):
            return True
        else:
            return False
