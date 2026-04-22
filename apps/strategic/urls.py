from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.strategic.views import GrantViewSet, ProgramViewSet, StrategicGoalViewSet

goals_router = DefaultRouter()
goals_router.register("", StrategicGoalViewSet, basename="strategic-goal")

grants_router = DefaultRouter()
grants_router.register("", GrantViewSet, basename="grant")

programs_router = DefaultRouter()
programs_router.register("", ProgramViewSet, basename="program")
