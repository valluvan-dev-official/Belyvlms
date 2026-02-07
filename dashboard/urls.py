from django.urls import path
from .api_views import (
    DashboardStatsView,
    DashboardGrowthView,
    DashboardDistributionView,
    DashboardScheduleView,
    DashboardMetricsView
)

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('growth-trend/', DashboardGrowthView.as_view(), name='dashboard-growth'),
    path('user-distribution/', DashboardDistributionView.as_view(), name='dashboard-distribution'),
    path('schedule/today/', DashboardScheduleView.as_view(), name='dashboard-schedule'),
    path('key-metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
]
