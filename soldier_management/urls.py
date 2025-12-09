from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('core.api.urls')),
]

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
