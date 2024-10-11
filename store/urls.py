from django.urls import path
from django.urls.conf import include
from rest_framework_nested import routers
from . import views
from .views import VendorViewSet, GuestOrderView
from .views import VendorOrderViewSet


router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='products')
router.register('collections', views.CollectionViewSet)
router.register('carts', views.CartViewSet)
router.register('customers', views.CustomerViewSet)
router.register('orders', views.OrderViewSet, basename='orders')
router.register('vendors', VendorViewSet)

products_router = routers.NestedDefaultRouter(
    router, 'products', lookup='product')
products_router.register('reviews', views.ReviewViewSet,
                         basename='product-reviews')
products_router.register('images', views.ProductImageViewSet, basename='product-images')


carts_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
carts_router.register('items', views.CartItemViewSet, basename='cart-items')

vendors_router = routers.NestedDefaultRouter(router, 'vendors', lookup='vendor')
vendors_router.register('images', views.VendorImageViewSet, basename='vendor-images')
router.register('vendor/orders', VendorOrderViewSet, basename='vendor-orders')
# URLConf
urlpatterns = router.urls + products_router.urls + carts_router.urls + vendors_router.urls + [
    path('guest-orders/', GuestOrderView.as_view(), name='guest-orders'),  # Add guest order retrieval as a direct URL
]
