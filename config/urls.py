"""URL configuration for CampusSpace project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.users.urls')),
    path('', include('apps.venues.urls')),
    path('schedules/', include('apps.schedules.urls')),
    path('maintenance/', include('apps.maintenance.urls')),
    path('bookings/', include('apps.bookings.urls')),
]

# 开发环境下添加静态文件和媒体文件URL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)