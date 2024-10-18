from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response

from store.serializers import ProductSerializer
from .models import LikedItem,  ContentType
from store.models import Product
class LikeProductView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, product_id):
        product = Product.objects.get(id=product_id)
        content_type = ContentType.objects.get_for_model(Product)

        # Check if the product is already liked
        liked_item, created = LikedItem.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=product_id
        )

        if not created:
            # If already liked, unlike the product
            liked_item.delete()
            return Response({'status': 'unliked'})
        else:
            # Like the product
            return Response({'status': 'liked'})


class LikeBasedRecommendationView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request):
        # Get the current user’s liked products
        user_likes = LikedItem.objects.filter(
            user=request.user,
            content_type=ContentType.objects.get_for_model(Product)
        )
        liked_product_ids = user_likes.values_list('object_id', flat=True)

        # Find other users who liked the same products
        similar_users = LikedItem.objects.filter(
            object_id__in=liked_product_ids
        ).exclude(user=request.user).values_list('user_id', flat=True)

        # Recommend products liked by similar users
        recommended_products_ids = LikedItem.objects.filter(
            user__in=similar_users
        ).values_list('object_id', flat=True).distinct()

        # Fetch the recommended products
        recommended_products = Product.objects.filter(id__in=recommended_products_ids)

        # Use the ProductSerializer to serialize the product data
        serializer = ProductSerializer(recommended_products, many=True)

        # Return the serialized data
        return Response(serializer.data)