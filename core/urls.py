# core/urls_panel.py
from django.urls import path
from .views import (
    panel_login, panel_logout, panel_dashboard,
    panel_soldiers, panel_leaves, panel_search
)

urlpatterns = [
    path('dashboard/login/', panel_login, name='panel_login'),
    path('dashboard/logout/', panel_logout, name='panel_logout'),
    path('dashboard/', panel_dashboard, name='panel_dashboard'),
    path('dashboard/soldiers/', panel_soldiers, name='panel_soldiers'),
    path('dashboard/leaves/', panel_leaves, name='panel_leaves'),
    path('dashboard/search/', panel_search, name='panel_search'),
]