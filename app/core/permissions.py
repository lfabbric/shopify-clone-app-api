from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Object-level permission to permit owners of the store or staff
    associated with the store make alterations.
    """

    def has_object_permission(self, request, view, obj):
        """
        For now, just return if the user matches
        We will use obj.user.store = request.user.profile.store
        or obj.user = request.user
        """

        return obj.user == request.user
