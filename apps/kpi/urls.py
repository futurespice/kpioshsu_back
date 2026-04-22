from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.kpi.views import (
    DepartmentKPIResultView,
    FacultyKPIResultView,
    KPIValueCreateView,
    KPIValueListView,
    KPIViewSet,
    TeacherKPIResultView,
    UniversityKPIResultView,
)

router = DefaultRouter()
router.register("", KPIViewSet, basename="kpi")

urlpatterns = [
    path("value/", KPIValueCreateView.as_view(), name="kpi-value-create"),
    path("value/<uuid:user_id>/", KPIValueListView.as_view(), name="kpi-value-list"),
    path(
        "result/teacher/<uuid:user_id>/",
        TeacherKPIResultView.as_view(),
        name="kpi-result-teacher",
    ),
    path(
        "result/department/<uuid:department_id>/",
        DepartmentKPIResultView.as_view(),
        name="kpi-result-department",
    ),
    path(
        "result/faculty/<uuid:faculty_id>/",
        FacultyKPIResultView.as_view(),
        name="kpi-result-faculty",
    ),
    path(
        "result/university/",
        UniversityKPIResultView.as_view(),
        name="kpi-result-university",
    ),
] + router.urls
