from django.urls import path

from apps.analytics.views import (
    DeanDepartmentsView,
    DeanOverviewView,
    DeanTeachersView,
    UniversityAlertsView,
    UniversityFacultyKpiView,
    UniversityGoalsView,
    UniversityHeatmapView,
    UniversityKpiTrendView,
    UniversityOverviewView,
    UniversityRadarView,
    ViceRectorDeptLoadView,
    ViceRectorOverviewView,
    ViceRectorSuccessDataView,
    ViceRectorUmkStatusView,
)

urlpatterns = [
    path("university/overview/", UniversityOverviewView.as_view()),
    path("university/kpi-trend/", UniversityKpiTrendView.as_view()),
    path("university/faculty-kpi/", UniversityFacultyKpiView.as_view()),
    path("university/radar/", UniversityRadarView.as_view()),
    path("university/heatmap/", UniversityHeatmapView.as_view()),
    path("university/goals/", UniversityGoalsView.as_view()),
    path("university/alerts/", UniversityAlertsView.as_view()),
    path("vice-rector/overview/", ViceRectorOverviewView.as_view()),
    path("vice-rector/dept-load/", ViceRectorDeptLoadView.as_view()),
    path("vice-rector/success-data/", ViceRectorSuccessDataView.as_view()),
    path("vice-rector/umk-status/", ViceRectorUmkStatusView.as_view()),
    path("dean/overview/", DeanOverviewView.as_view()),
    path("dean/teachers/", DeanTeachersView.as_view()),
    path("dean/departments/", DeanDepartmentsView.as_view()),
]
