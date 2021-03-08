from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication

from core.models import Store, Product
from core.permissions import IsOwnerOrReadOnly
from store import serializers


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


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)

    def get_queryset(self):
        """retrieve products filtered by store"""
        queryset = self.queryset
        store_slug = self.kwargs['slug']

        return queryset.filter(store__slug=store_slug)
