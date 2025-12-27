from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


def root_redirect(request):
    return redirect('panel_dashboard')


urlpatterns = [
    path('', root_redirect, name='root'),

    path('dashboard/', include('core.urls')),

    path('admin/', admin.site.urls),
    path('api/', include('core.api.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
]

handler404 = 'core.views_core.page_not_found'
handler500 = 'core.views_core.server_error'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
