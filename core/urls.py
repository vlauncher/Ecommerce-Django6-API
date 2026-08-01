from django.contrib import admin
from django.urls import path, include
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
    # API v1 Auth Endpoints
    path("api/v1/auth/", include("accounts.urls")),
]
