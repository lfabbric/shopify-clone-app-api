from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status, mixins, permissions
from rest_framework.authentication import TokenAuthentication

from core.models import Store, Product, Collection, \
                        ProductImage, ProductAttachment
from core import utils
from core.permissions import IsOwnerOrReadOnly, IsOwnerOrStaff
from store import serializers

from django.utils import timezone


class StoreViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StoreSerializer
    queryset = Store.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsOwnerOrReadOnly,)
    lookup_field = 'slug'

    def get_queryset(self):
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == 'upload_image':
            return serializers.StoreImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, slug=None):
        """Upload an image to a store"""
        store = Store.objects.filter(slug=slug).first()
        serializer = self.get_serializer(
            store,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class PublicStoreReadOnlyViewSet(viewsets.GenericViewSet,
                                 mixins.ListModelMixin,
                                 mixins.RetrieveModelMixin):

    def get_queryset(self):
        """Return objects for the base store"""
        queryset = self.queryset
        store_slug = self.kwargs['store']

        return queryset.filter(store__slug=store_slug)


class BaseStoreModelViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff,)

    def get_queryset(self):
        """Return objects for the base store"""
        queryset = self.queryset
        store_slug = self.kwargs['store']

        return queryset.filter(store__slug=store_slug)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(PublicStoreReadOnlyViewSet):
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        queryset = super().get_queryset().filter(
            published=True,
            date_available__lte=timezone.now()
        )

        if tags:
            queryset = queryset.filter(
                tags__name__in=utils.comma_splitter(tags)
            ).distinct()
        return queryset


class ProductAdminViewSet(BaseStoreModelViewSet):
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()


class CollectionViewSet(PublicStoreReadOnlyViewSet):
    serializer_class = serializers.CollectionSerializer
    queryset = Collection.objects.all()

    @action(methods=['GET'], detail=True, url_path='collection-product-list')
    def product_list(self, request, store, pk):
        collection = Collection.objects.get(pk=pk, store__slug=store)
        products = collection.get_products()
        serializer = serializers.ProductSerializer(products, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class ProductImageViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff,)
    serializer_class = serializers.ProductImageSerializer
    queryset = ProductImage.objects.all()

    def get_queryset(self):
        """Return objects for the base store"""
        return self.queryset.filter(
            product__store__slug=self.kwargs['store'],
            product__id=self.kwargs['product_pk']
        )


class ProductAttachmentViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff,)
    serializer_class = serializers.ProductAttachmentSerializer
    queryset = ProductAttachment.objects.all()

    def get_queryset(self):
        """Return objects for the base store"""
        return self.queryset.filter(
            product__store__slug=self.kwargs['store'],
            product__id=self.kwargs['product_pk']
        )
