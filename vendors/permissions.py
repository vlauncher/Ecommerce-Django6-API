from rest_framework.permissions import BasePermission


class IsVendorOwner(BasePermission):
    """Ensures the requesting user owns the vendor profile."""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        elif hasattr(obj, "vendor"):
            return obj.vendor.owner == request.user
        return False


class IsActiveVendor(BasePermission):
    """Ensures the requesting user has an active vendor profile."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "vendor_profile")
            and request.user.vendor_profile.status == "active"
        )
