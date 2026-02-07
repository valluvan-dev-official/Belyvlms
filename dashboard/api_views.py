from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rbac.permissions import HasRBACPermission
from .services import DashboardService

class DashboardBaseView(APIView):
    """
    Base view for Dashboard endpoints.
    Enforces Authentication and Dashboard Role Permission.
    """
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'DASHBOARD_VIEW_GLOBAL'

    def get_service(self, request):
        active_role = request.headers.get('X-Active-Role')
        return DashboardService(request.user, active_role)

class DashboardStatsView(DashboardBaseView):
    """
    GET /api/dashboard/stats/
    Returns hero stats cards.
    """
    @swagger_auto_schema(
        operation_summary="Get Hero Stats",
        operation_description="Returns high-level stats cards (Total Students, Active Batches, etc.) scoped by the user's active role.",
        manual_parameters=[
            openapi.Parameter('X-Active-Role', openapi.IN_HEADER, description="Active Role Code (ADMIN, TRAINER, STUDENT)", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'label': openapi.Schema(type=openapi.TYPE_STRING, example="Total Students"),
                        'value': openapi.Schema(type=openapi.TYPE_INTEGER, example=120),
                        'trend': openapi.Schema(type=openapi.TYPE_STRING, example="+5%"),
                        'color': openapi.Schema(type=openapi.TYPE_STRING, example="blue"),
                    }
                )
            )
        }
    )
    def get(self, request):
        service = self.get_service(request)
        data = service.get_hero_stats()
        return Response(data, status=status.HTTP_200_OK)

class DashboardGrowthView(DashboardBaseView):
    """
    GET /api/dashboard/growth-trend/
    Returns growth trend chart data.
    """
    @swagger_auto_schema(
        operation_summary="Get Growth Trend",
        operation_description="Returns monthly enrollment data for the growth line chart.",
        manual_parameters=[
            openapi.Parameter('X-Active-Role', openapi.IN_HEADER, description="Active Role Code (ADMIN, TRAINER, STUDENT)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('period', openapi.IN_QUERY, description="Time period (e.g., 6m, 1y)", type=openapi.TYPE_STRING, default='6m')
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'xAxis': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING, example="Jan"),
                        description="Labels for the X-Axis (Months)"
                    ),
                    'series': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'name': openapi.Schema(type=openapi.TYPE_STRING, example="Total Students"),
                                'data': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_INTEGER, example=120)
                                ),
                            }
                        )
                    )
                }
            )
        }
    )
    def get(self, request):
        period = request.query_params.get('period', '6m')
        service = self.get_service(request)
        data = service.get_growth_trend(period)
        return Response(data, status=status.HTTP_200_OK)

class DashboardDistributionView(DashboardBaseView):
    """
    GET /api/dashboard/user-distribution/
    Returns user distribution data (e.g. by status).
    """
    @swagger_auto_schema(
        operation_summary="Get User Distribution",
        operation_description="Returns distribution data (e.g., Active vs Inactive, Course Status) for pie/bar charts.",
        manual_parameters=[
            openapi.Parameter('X-Active-Role', openapi.IN_HEADER, description="Active Role Code (ADMIN, TRAINER, STUDENT)", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'categories': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING, example="Jan"),
                        description="Time categories (Months)"
                    ),
                    'active_data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_INTEGER, example=150),
                        description="Active User Counts per Month"
                    ),
                    'inactive_data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                        description="Inactive User Counts per Month"
                    ),
                }
            )
        }
    )
    def get(self, request):
        service = self.get_service(request)
        data = service.get_distribution_data()
        return Response(data, status=status.HTTP_200_OK)

class DashboardScheduleView(DashboardBaseView):
    """
    GET /api/dashboard/schedule/today/
    Returns today's schedule.
    """
    @swagger_auto_schema(
        operation_summary="Get Today's Schedule",
        operation_description="Returns the list of classes scheduled for today based on active batches.",
        manual_parameters=[
            openapi.Parameter('X-Active-Role', openapi.IN_HEADER, description="Active Role Code (ADMIN, TRAINER, STUDENT)", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        'title': openapi.Schema(type=openapi.TYPE_STRING, example="Batch A - Python"),
                        'time': openapi.Schema(type=openapi.TYPE_STRING, example="10:00 AM - 12:00 PM"),
                        'trainer': openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
                        'type': openapi.Schema(type=openapi.TYPE_STRING, example="Online"),
                    }
                )
            )
        }
    )
    def get(self, request):
        service = self.get_service(request)
        data = service.get_schedule_today()
        return Response(data, status=status.HTTP_200_OK)

class DashboardMetricsView(DashboardBaseView):
    """
    GET /api/dashboard/key-metrics/
    Returns right sidebar metrics.
    """
    @swagger_auto_schema(
        operation_summary="Get Key Metrics",
        operation_description="Returns secondary metrics for the sidebar.",
        manual_parameters=[
            openapi.Parameter('X-Active-Role', openapi.IN_HEADER, description="Active Role Code (ADMIN, TRAINER, STUDENT)", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
        }
    )
    def get(self, request):
        # Reusing hero stats logic or implementing specific sidebar logic
        # For now, let's return a subset of stats or specific alerts
        service = self.get_service(request)
        # Using a lightweight method if it existed, or just empty for now
        return Response([], status=status.HTTP_200_OK)
