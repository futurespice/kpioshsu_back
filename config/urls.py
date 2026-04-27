from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from apps.strategic.urls import goals_router, grants_router, programs_router

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/", include("apps.auth.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/faculties/", include("apps.faculties.urls")),
    path("api/departments/", include("apps.departments.urls")),
    path("api/kpi/", include("apps.kpi.urls")),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/publications/", include("apps.publications.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/approvals/", include("apps.approvals.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/planerka/", include("apps.planerka.urls")),
    path("api/load/", include("apps.department_load.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/strategic-goals/", include(goals_router.urls)),
    path("api/grants/", include(grants_router.urls)),
    path("api/programs/", include(programs_router.urls)),
    path("api/export/", include("apps.export.urls")),
]
