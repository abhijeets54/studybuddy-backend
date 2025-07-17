from django.urls import path
from . import views

urlpatterns = [
    # Dashboard endpoint
    path('overview/', views.dashboard_stats, name='analytics-overview'),
    path('dashboard/', views.dashboard_stats, name='dashboard-stats'),  # Keep for backward compatibility
]
