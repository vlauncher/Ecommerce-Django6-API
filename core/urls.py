from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Redoc UI at root path
    path("", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Swagger UI at /docs/
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # OpenAPI Schema endpoint
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Django Admin
    path("admin/", admin.site.urls),
    # API v1 Endpoints
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/vendors/", include("vendors.urls")),
    path("api/v1/catalog/", include("catalog.urls")),
    path("api/v1/reviews/", include("reviews.urls")),
    path("api/v1/cart/", include("cart.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/payments/", include("payments.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

