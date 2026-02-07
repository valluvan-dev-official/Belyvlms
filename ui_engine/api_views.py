from rest_framework import views, status, permissions
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .services import UIService
from .serializers import UIConfigSerializer

class UIConfigView(views.APIView):
    """
    API to fetch UI Layout/Metadata for the current user context.
    Driven by Role Defaults and User Preferences.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get UI Configuration",
        operation_description="Returns the layout, tabs, and widget configuration for the requested module (e.g., dashboard).",
        manual_parameters=[
            openapi.Parameter('X-Active-Role', openapi.IN_HEADER, description="Active Role Code (ADMIN, TRAINER, STUDENT)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('module', openapi.IN_QUERY, description="Module Slug (default: dashboard)", type=openapi.TYPE_STRING, default='dashboard')
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'config': openapi.Schema(type=openapi.TYPE_OBJECT, description="The JSON layout config"),
                    'version': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'source': openapi.Schema(type=openapi.TYPE_STRING, description="Source of config (role_default vs user_preference)")
                }
            )
        }
    )
    def get(self, request):
        active_role = request.headers.get('X-Active-Role')
        if not active_role:
             return Response({"error": "X-Active-Role header missing"}, status=status.HTTP_400_BAD_REQUEST)

        module_slug = request.query_params.get('module', 'dashboard')
        
        service = UIService()
        data = service.get_ui_config(request.user, active_role, module_slug)
        
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Save User Preference",
        operation_description="Saves a personalized layout override for the current user.",
        manual_parameters=[
            openapi.Parameter('X-Active-Role', openapi.IN_HEADER, description="Active Role Code", type=openapi.TYPE_STRING, required=True),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'module': openapi.Schema(type=openapi.TYPE_STRING, default='dashboard'),
                'config': openapi.Schema(type=openapi.TYPE_OBJECT, description="The full JSON config to save")
            },
            required=['config']
        ),
        responses={200: "Preference Saved"}
    )
    def post(self, request):
        active_role = request.headers.get('X-Active-Role')
        if not active_role:
             return Response({"error": "X-Active-Role header missing"}, status=status.HTTP_400_BAD_REQUEST)

        module_slug = request.data.get('module', 'dashboard')
        config_data = request.data.get('config')
        
        if not config_data:
            return Response({"error": "Config data is required"}, status=status.HTTP_400_BAD_REQUEST)

        service = UIService()
        result = service.save_user_preference(request.user, active_role, module_slug, config_data)
        
        if "error" in result:
             return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
