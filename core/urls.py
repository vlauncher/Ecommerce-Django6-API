from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from ninja import NinjaAPI
from apps.users.api import auth_router, user_router

api = NinjaAPI(
    title="Ecommerce Django 6 API",
    version="1.0.0",
    description="Scalable, reliable, async-native Django 6.0 API built with Django Ninja",
    docs_url="/docs",
)

api.add_router("/api/v1/auth/", auth_router)
api.add_router("/api/v1/users/", user_router)

from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

