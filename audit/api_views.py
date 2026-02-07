from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rbac.permissions import HasRBACPermission
from drf_yasg.utils import swagger_auto_schema
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = "AUDIT_LOG_VIEW"

    @swagger_auto_schema(tags=["Audit"])
    @action(detail=False, methods=["get"])
    def export(self, request):
        self.required_permission = "AUDIT_LOG_EXPORT"
        logs = self.get_queryset()[:1000]
        data = AuditLogSerializer(logs, many=True).data
        return Response({"count": len(data), "items": data})
