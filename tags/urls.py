from django.urls import path

from .views import ProductRecommendationView, AddTagToProductView

urlpatterns = [
    path('recommend-products/<int:product_id>/', ProductRecommendationView.as_view(), name='recommend-products'),
    path('add-tag-to-product/<int:product_id>/', AddTagToProductView.as_view(), name='add-tag-to-product'),
]
