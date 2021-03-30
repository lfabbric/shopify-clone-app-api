from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions, mixins
from rest_framework.authentication import TokenAuthentication

from core.models import Shipping, Order, Cart, Store, Product
from core.permissions import IsOwnerOrStaff
from commerce import serializers


class ShippingViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff,)
    serializer_class = serializers.ShippingSerializer
    queryset = Shipping.objects.all()

    def get_queryset(self):
        """Return objects for the base store"""
        queryset = self.queryset
        store_slug = self.kwargs['store']
        userid = self.request.query_params.get('userid', None)

        if userid:
            return queryset.filter(
                store__slug=store_slug,
                user__id=userid
            ).order_by('-updated_at')

        return self.queryset.filter(store__slug=store_slug)

    @action(methods=['GET'], detail=False, url_path='shipping-active')
    def get_active(self, request, store=None, *args):
        userid = self.request.query_params.get('userid', None)

        if userid:
            queryset = self.get_queryset()
            shipto = queryset[:1].get()
            serializer = serializers.ShippingSerializer(shipto, many=False)
            return Response(serializer.data)

        return Response(
            {'status': 'no userid defined'},
            status=status.HTTP_400_BAD_REQUEST
        )


class StoreOwnerOrderViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff,)
    serializer_class = serializers.OrderSerializer
    queryset = Order.objects.all()


class CustomerOrderViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff,)
    serializer_class = serializers.OrderSerializer
    queryset = Order.objects.all()


class CartViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    lookup_field = 'id'
    authentication_classes = (TokenAuthentication,)
    serializer_class = serializers.CartSerializer
    queryset = Cart.objects.all()

    def create(self, request, store=None, *args, **kwargs):
        """
        Possible issue with spamming url can create unlimited entries in
        the cart table.  Find a way to throttle and test
        """
        store = Store.objects.get(slug=store)
        user = self.request.user
        if request.user.is_anonymous:
            user = None
        cart = Cart.objects.create(
            store=store,
            user=user
        )
        serializer = serializers.CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [
                permissions.IsAuthenticated, IsOwnerOrStaff,
            ]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Return objects for the base store"""
        queryset = self.queryset
        store_slug = self.kwargs['store']
        user = self.request.user

        if user:
            return queryset.filter(
                store__slug=store_slug,
                user=user
            )
        id = self.request.query_params.get('id', None)
        return queryset.filter(
            store__slug=store_slug,
            id=id
        )

    @action(methods=['POST'], detail=True, url_path='add-to-cart')
    def add_to_cart(self, request, store, id, *args, **kwargs):
        store = Store.objects.get(slug=store)
        cart = Cart.objects.get(id=id)
        # use get_object()
        product_id = request.data.get('product_id', None)
        product = Product.objects.get(store=store, id=product_id)
        if product:
            quantity = request.data.get('quantity', 1)
            note = request.data.get('note', '')
            cart.add(product, quantity, note)
            serializer = serializers.CartSerializer(cart, many=False)
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['POST'], detail=True, url_path='remove-from-cart')
    def remove_from_cart(self, request, store, id, *args, **kwargs):
        store = Store.objects.get(slug=store)
        cart = Cart.objects.get(id=id)
        product_id = request.data.get('product_id', None)
        product = Product.objects.get(store=store, id=product_id)

        if product:
            cart.remove(product)
            serializer = serializers.CartSerializer(cart, many=False)
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
