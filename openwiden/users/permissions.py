from rest_framework import permissions


class IsUserOrAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj) -> bool:

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user or request.user.is_superuser
