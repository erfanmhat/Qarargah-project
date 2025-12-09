from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.api.views import SoldierViewSet, LeaveViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'soldiers', SoldierViewSet, basename='soldier')
router.register(r'leaves', LeaveViewSet, basename='leave')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]

