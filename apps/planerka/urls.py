from rest_framework.routers import DefaultRouter

from apps.planerka.views import PlanerkaViewSet

router = DefaultRouter()
router.register("", PlanerkaViewSet, basename="planerka")

urlpatterns = router.urls
