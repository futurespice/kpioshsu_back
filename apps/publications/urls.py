from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.publications.views import PublicationStatsView, PublicationViewSet

router = DefaultRouter()
router.register("", PublicationViewSet, basename="publication")

urlpatterns = [
    path(
        "stats/<uuid:user_id>/",
        PublicationStatsView.as_view(),
        name="publication-stats",
    ),
] + router.urls
