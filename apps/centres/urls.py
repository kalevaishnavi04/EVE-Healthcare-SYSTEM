from rest_framework.routers import DefaultRouter

from .views import DiagnosticCentreViewSet, DiagnosticTestViewSet

router = DefaultRouter()
router.register("centres", DiagnosticCentreViewSet, basename="centre")
router.register("tests", DiagnosticTestViewSet, basename="test")

urlpatterns = router.urls
