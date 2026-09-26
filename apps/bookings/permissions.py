from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Object-level permission: only the booking's own user may access it."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
