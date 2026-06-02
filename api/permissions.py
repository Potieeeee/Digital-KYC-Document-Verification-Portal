from rest_framework.permissions import BasePermission


class IsOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.groups.filter(name__in=["Reviewer", "Manager", "Admin"]).exists():
            return True

        return obj.user == request.user

class IsReviewerManagerAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(
            name__in=["Reviewer", "Manager", "Admin"]
        ).exists()


class IsThirdPartyAPI(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(
            name="ThirdPartyAPI"
        ).exists()