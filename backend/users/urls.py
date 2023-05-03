from rest_framework.routers import DefaultRouter

from .views import SubscribitionViewSet, UserViewSet

router = DefaultRouter()
router.register(r'subscriptions', SubscribitionViewSet,
                basename='subscripitions')
router.register(r'', UserViewSet)


urlpatterns = []
urlpatterns += router.urls
