from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from cars.views import CarViewSet, car_list
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r"cars", CarViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/cars/', car_list),   # GET с фильтрацией для бота
    path('api/', include(router.urls)),  # полный CRUD через DRF
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
