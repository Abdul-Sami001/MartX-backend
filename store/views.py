from rest_framework.views import APIView
from rest_framework import status
from payments.models import Payment
from store.permissions import FullDjangoModelPermissions, IsAdminOrReadOnly, ViewCustomerHistoryPermission
from store.pagination import DefaultPagination
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import status
from .filters import ProductFilter
from .models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product, Review, ProductImage, Vendor, \
    VendorImage
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CollectionSerializer, \
    CreateOrderSerializer, CustomerSerializer, OrderSerializer, ProductSerializer, ReviewSerializer, \
    UpdateCartItemSerializer, UpdateOrderSerializer, ProductImageSerializer, VendorSerializer, VendorImageSerializer, \
    AuthenticatedOrderSerializer, GuestOrderSerializer
import logging
from store.models import Customer

class ProductViewSet(ModelViewSet):
    queryset = Product.objects.prefetch_related("images").all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Product cannot be deleted because it is associated with an order item.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(
        products_count=Count('products')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']):
            return Response({'error': 'Collection cannot be deleted because it includes one or more products.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        return CartItem.objects \
            .filter(cart_id=self.kwargs['cart_pk']) \
            .select_related('product')


class VendorViewSet(ModelViewSet):
    queryset = Vendor.objects.filter(is_verified=True).prefetch_related("images").all()
    serializer_class = VendorSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user')
        if not user_id:
            return Response({'error': 'User field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is already linked to a vendor
        if Vendor.objects.filter(user_id=user_id).exists():
            return Response({'error': 'This user is already linked to a vendor.'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['get'], url_path='products')
    def list_products(self, request, pk=None):
        vendor = self.get_object()
        products = vendor.products.all()
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response('ok')

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = Customer.objects.get(
            user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)




logger = logging.getLogger(__name__)

from rest_framework import status
from rest_framework.response import Response
from .models import Customer, Cart, CartItem, Order


# class OrderViewSet(ModelViewSet):
#     http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
#
#     def get_permissions(self):
#         if self.request.method in ['PATCH', 'DELETE']:
#             return [IsAdminUser()]
#         elif self.request.method == 'POST':
#             return [AllowAny()]  # Allow both authenticated and unauthenticated users to create an order
#         return [IsAuthenticated()]  # Ensure users are authenticated for GET requests
#
#     def create(self, request, *args, **kwargs):
#         # Decide which serializer to use based on whether the user is authenticated or not
#         if request.user.is_authenticated:
#             serializer = AuthenticatedOrderSerializer(
#                 data=request.data,
#                 context={'user': request.user}
#             )
#         else:
#             serializer = GuestOrderSerializer(
#                 data=request.data,
#                 context={'request': request}
#             )
#
#         # Validate the data
#         serializer.is_valid(raise_exception=True)
#
#         # Save the order (this will handle the logic of both authenticated and guest users)
#         order = serializer.save()
#
#         # Check if a payment already exists for this order
#         existing_payment = Payment.objects.filter(order=order).first()
#
#         if existing_payment:
#             # If payment exists and is COMPLETED, return an error
#             if existing_payment.status == Payment.COMPLETED:
#                 return Response({'error': f"Payment for Order {order.id} has already been completed."},
#                                 status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 # If payment exists but is PENDING or FAILED, allow retry by updating its status
#                 existing_payment.status = Payment.PENDING  # or keep FAILED for retry handling
#                 existing_payment.save()
#                 payment = existing_payment  # Reuse the existing payment for the retry
#         else:
#             # Create a new payment if no payment exists
#             total_amount = order.calculate_total_amount()  # Make sure this method exists on your model
#             payment = Payment.objects.create(
#                 order=order,
#                 amount=total_amount,
#                 status=Payment.PENDING,
#                 payment_method='stripe'  # This could be dynamic based on the user’s choice
#             )
#
#         # Serialize the order for response
#         serializer = OrderSerializer(order)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             if self.request.user.is_authenticated:
#                 return AuthenticatedOrderSerializer
#             else:
#                 return GuestOrderSerializer
#         elif self.request.method == 'PATCH':
#             return UpdateOrderSerializer
#         return OrderSerializer
class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        elif self.request.method == 'POST':
            return [AllowAny()]  # Allow both authenticated and unauthenticated users to create an order
        return [IsAuthenticated()]  # Ensure users are authenticated for GET requests

    def create(self, request, *args, **kwargs):
        # Decide which serializer to use based on whether the user is authenticated or not
        if request.user.is_authenticated:
            serializer = AuthenticatedOrderSerializer(
                data=request.data,
                context={'user': request.user}
            )
        else:
            serializer = GuestOrderSerializer(
                data=request.data,
                context={'request': request}
            )

        # Validate the data
        serializer.is_valid(raise_exception=True)

        # Save the order (this will handle the logic of both authenticated and guest users)
        order = serializer.save()

        # Get payment method from the request
        payment_method = request.data.get('payment_method', 'stripe')  # Default to 'stripe' if not provided

        if payment_method.lower() == 'cod':
            # If the payment method is Cash on Delivery (COD)
            payment_status = Payment.PENDING  # COD payments are typically marked as 'pending' initially
            payment_method = 'COD'
        else:
            # For other payment methods like Stripe, default to 'stripe' logic
            payment_status = Payment.PENDING  # Adjust as needed

        # Create a new payment record for the order
        total_amount = order.calculate_total_amount()  # Ensure this method exists in your Order model
        payment = Payment.objects.create(
            order=order,
            amount=total_amount,
            status=payment_status,
            payment_method=payment_method
        )

        # Serialize the order for response
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            if self.request.user.is_authenticated:
                return AuthenticatedOrderSerializer
            else:
                return GuestOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Order.objects.all()

        if user.is_authenticated:
            customer_id = Customer.objects.only('id').get(user_id=user.id)
            return Order.objects.filter(customer_id=customer_id)

        # For guest users, returning none as they cannot view their orders unless implemented separately
        return Order.objects.none()







class ProductImageViewSet(ModelViewSet):
    serializer_class = ProductImageSerializer
    
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}
    
    def get_queryset(self):
        return ProductImage.objects.filter(product_id = self.kwargs['product_pk'])


class VendorImageViewSet(ModelViewSet):
    serializer_class = VendorImageSerializer

    def get_serializer_context(self):
        return {'vendor_id': self.kwargs['vendor_pk']}

    def get_queryset(self):
        return VendorImage.objects.filter(vendor_id=self.kwargs['vendor_pk'])




class GuestOrderView(APIView):
    """
    This view allows guest users to retrieve their order details using order_id or email.
    No authentication required.
    """
    permission_classes = []  # No authentication required

    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        email = request.data.get('email')

        if not order_id and not email:
            return Response({"error": "Either Order ID or email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the order based on order_id or email
            if order_id:
                order = Order.objects.get(id=order_id)
            elif email:
                order = Order.objects.filter(customer__user__email=email).first()  # Get the first matching order

            # If order is not found
            if not order:
                return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

            # Serialize the order details
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)



class VendorOrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get the vendor associated with the logged-in user
        vendor = Vendor.objects.get(user=self.request.user)

        # Get the orders for products that belong to this vendor
        return Order.objects.filter(items__product__vendor=vendor).distinct()

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        order = self.get_object()

        # Ensure the vendor can only update their own orders
        if not OrderItem.objects.filter(order=order, product__vendor=Vendor.objects.get(user=self.request.user)).exists():
            return Response({'error': 'You do not have permission to update this order.'}, status=status.HTTP_403_FORBIDDEN)

        # Update the order's payment status if valid
        order_status = request.data.get('status')  # Rename local variable to avoid conflict with status module
        if order_status:
            order.payment_status = order_status
            order.save()
            return Response({'status': 'Order status updated'}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
