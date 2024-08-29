from django.contrib import admin
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from uuid import uuid4

from django.db.models import Avg

from .validators import validate_file_size

class Promotion(models.Model):
    description = models.CharField(max_length=255)
    discount = models.FloatField()


class Collection(models.Model):
    title = models.CharField(max_length=255)
    featured_product = models.ForeignKey(
        'Product', on_delete=models.SET_NULL, null=True, related_name='+', blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['title']


class Vendor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Link to User or Seller
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    shop_name = models.CharField(max_length=255)
    shop_description = models.TextField(null=True, blank=True)
    shop_address = models.CharField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False)  # Admin verification status

    def average_rating(self):
        # Aggregate the average rating of all products associated with this vendor
        return self.products.aggregate(Avg('reviews__rating'))['reviews__rating__avg'] or 0.0

    def __str__(self):
        return self.shop_name


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(1)])
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(
        Collection, on_delete=models.PROTECT, related_name='products')
    promotions = models.ManyToManyField(Promotion, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='products', null=True, blank=True) #Remove null and blank
    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ['title']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete= models.CASCADE)
    image = models.ImageField(upload_to = r'store\images', validators = [validate_file_size])


class Customer(models.Model):
    phone = models.CharField(max_length=20)
    address = models.CharField(null=True, max_length=255)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name

    @admin.display(ordering='user__last_name')
    def last_name(self):
        return self.user.last_name

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        permissions = [
            ('view_history', 'Can view history')
        ]


class Order(models.Model):
    PAYMENT_STATUS_PENDING = 'P'
    PAYMENT_STATUS_COMPLETE = 'C'
    PAYMENT_STATUS_FAILED = 'F'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_COMPLETE, 'Complete'),
        (PAYMENT_STATUS_FAILED, 'Failed')
    ]

    placed_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)

    class Meta:
        permissions = [
            ('cancel_order', 'Can cancel order')
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='addresses')


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = [['cart', 'product']]


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=255)  # Name of the reviewer
    description = models.TextField()  # Review content
    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True)  # Rating out of 5
    date = models.DateField(auto_now_add=True)  # Date when the review was created

    def __str__(self):
        return f'{self.name} - {self.rating} Stars'

