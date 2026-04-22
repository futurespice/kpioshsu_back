from django.urls import path

from apps.export.views import (
    DepartmentKPIExportView,
    FacultyKPIExportView,
    PublicationsExportView,
    TasksExportView,
    TeacherKPIExportView,
    UniversityReportExportView,
)

urlpatterns = [
    path("kpi/teacher/<uuid:user_id>/", TeacherKPIExportView.as_view()),
    path("kpi/department/<uuid:department_id>/", DepartmentKPIExportView.as_view()),
    path("kpi/faculty/<uuid:faculty_id>/", FacultyKPIExportView.as_view()),
    path("tasks/", TasksExportView.as_view()),
    path("publications/<uuid:user_id>/", PublicationsExportView.as_view()),
    path("report/university/", UniversityReportExportView.as_view()),
]
