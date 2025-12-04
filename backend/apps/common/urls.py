"""
URL configuration for common endpoints
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('health/detailed/', views.health_check_detailed, name='health-check-detailed'),
    path('health/ready/', views.readiness_check, name='readiness-check'),
    path('health/live/', views.liveness_check, name='liveness-check'),
    path('metrics/', views.metrics, name='metrics'),
]
