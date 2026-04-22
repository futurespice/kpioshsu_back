from rest_framework.routers import DefaultRouter

from apps.department_load.views import DeptLoadViewSet

router = DefaultRouter()
router.register("departments", DeptLoadViewSet, basename="dept-load")

urlpatterns = router.urls
