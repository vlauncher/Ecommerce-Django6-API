from django.urls import path
from search.views import ProductSearchView, SearchSuggestionView

urlpatterns = [
    path("products/", ProductSearchView.as_view(), name="search-products"),
    path("suggestions/", SearchSuggestionView.as_view(), name="search-suggestions"),
]
