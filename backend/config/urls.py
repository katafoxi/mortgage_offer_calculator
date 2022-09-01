from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView

from calc.views import *
from .routers import router

router.register(r"offer", OfferViewSet, basename='offer')
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("", Calculator.as_view(), name='main'),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path("api/__debug__/", include(debug_toolbar.urls)),
                  ] + urlpatterns
