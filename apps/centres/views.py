from rest_framework import filters, permissions, viewsets

from .models import DiagnosticCentre, DiagnosticTest
from .serializers import DiagnosticCentreSerializer, DiagnosticTestSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Anyone (even anonymous) can browse centres/tests; only staff can manage them."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class DiagnosticCentreViewSet(viewsets.ModelViewSet):
    """
    list, retrieve: public.
    create, update, destroy: admin/staff only.
    """

    queryset = DiagnosticCentre.objects.filter(is_active=True).prefetch_related("tests")
    serializer_class = DiagnosticCentreSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "location"]


class DiagnosticTestViewSet(viewsets.ModelViewSet):
    """
    list, retrieve: public. Supports ?centre=<id> to filter by centre.
    create, update, destroy: admin/staff only.
    """

    queryset = DiagnosticTest.objects.filter(is_active=True).select_related("centre")
    serializer_class = DiagnosticTestSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "centre__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        centre_id = self.request.query_params.get("centre")
        if centre_id:
            qs = qs.filter(centre_id=centre_id)
        return qs
