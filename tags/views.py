from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response

from store.serializers import ProductSerializer
from tags.models import TaggedItem, Tag
from django.contrib.contenttypes.models import ContentType
from store.models import Product
# Create your views here.
class ProductRecommendationView(APIView):
    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)

        # Get the content type for Product model
        content_type = ContentType.objects.get_for_model(Product)

        # Find tags for the current product
        tags = TaggedItem.objects.filter(
            content_type=content_type,
            object_id=product_id
        ).values_list('tag', flat=True)

        # Find all products with the same tags (excluding the current product)
        recommended_products_ids = TaggedItem.objects.filter(
            tag__in=tags,
            content_type=content_type
        ).exclude(object_id=product_id).values_list('object_id', flat=True)

        # Fetch the actual product objects
        recommended_products = Product.objects.filter(id__in=recommended_products_ids)

        # Serialize the product data using the ProductSerializer
        serializer = ProductSerializer(recommended_products, many=True)

        # Return the serialized data in the response
        return Response(serializer.data)


class AddTagToProductView(APIView):
    def post(self, request, product_id):
        tag_label = request.data.get('tag')
        product = Product.objects.get(id=product_id)
        content_type = ContentType.objects.get_for_model(Product)

        # Check if tag exists, otherwise create it
        tag, created = Tag.objects.get_or_create(label=tag_label)

        # Create TaggedItem
        TaggedItem.objects.get_or_create(
            tag=tag,
            content_type=content_type,
            object_id=product.id
        )

        return Response({'status': 'tag added'})


# class ProductRecommendationView(APIView):
#     def get(self, request, product_id):
#         product = Product.objects.get(id=product_id)
#         tags = TaggedItem.objects.get_tags_for(Product, product_id)
#
#         # Get all products with the same tags
#         recommended_products = Product.objects.filter(
#             taggeditem__tag__in=tags.values_list('tag', flat=True)
#         ).exclude(id=product_id).distinct()
#
#         recommendations = recommended_products.values('id', 'title', 'unit_price')
#         return Response(recommendations)