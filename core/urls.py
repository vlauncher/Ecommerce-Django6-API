from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from ninja import NinjaAPI
from ninja.openapi.docs import Redoc
from apps.users.api import auth_router, user_router
from apps.shops.api import invitation_router, shop_router
from apps.catalog.api import catalog_router
from apps.commerce.api import commerce_router
from apps.payments.api import payment_router
from apps.interactions.api import interaction_router
from apps.management_api.api import management_router

api = NinjaAPI(
    title="Ecommerce Django 6 API",
    version="1.0.0",
    description="Scalable, reliable, async-native Django 6.0 API built with Django Ninja",
    docs_url="/docs",
)

api.add_router("/api/v1/auth/", auth_router)
api.add_router("/api/v1/users/", user_router)
api.add_router("/api/v1/shops/", shop_router)
api.add_router("/api/v1/invitations/", invitation_router)
api.add_router("/api/v1/", catalog_router)
api.add_router("/api/v1/", commerce_router)
api.add_router("/api/v1/payments/", payment_router)
api.add_router("/api/v1/", interaction_router)
api.add_router("/api/v1/manage/", management_router)


def redoc_view(request):
    return Redoc().render_page(request, api)

from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", redoc_view, name="redoc"),
    path("", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
