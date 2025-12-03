from django.urls import path
from .views import admin_dashboard, soldier_search_view

urlpatterns = [
    path('', admin_dashboard, name='admin_dashboard'),
    path('soldiers/search/', soldier_search_view, name='soldier_search'),
]
