from rest_framework import serializers
from core.models import Shipping, Order, Cart, CartItem
from user.serializers import UserSerializer
from store.serializers import SimpleProductSerializer


class ShippingSerializer(serializers.ModelSerializer):
    """"Serialize a shipping address"""
    city = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='slug'
    )
    state = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='slug'
    )
    country = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='slug'
    )
    user = UserSerializer()

    class Meta:
        model = Shipping
        fields = (
            'id', 'company', 'address', 'suite', 'postal_code',
            'telephone', 'user', 'city', 'state', 'country'
        )
        read_only_fields = ('id', 'updated_at', 'created_at',)


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Order
        fields = (
            'id', 'status', 'user', 'final_amount', 'currency',
            'is_paid'
        )
        read_only_fields = ('id', 'updated_at', 'created_at',)


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(many=False, read_only=True)

    class Meta:
        model = CartItem
        fields = (
            'id', 'price', 'quantity', 'product'
        )
        read_only_fields = ('id', 'updated_at', 'created_at',)


class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    cart_items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = (
            'id', 'user', 'amount', 'currency', 'cart_items'
        )
        read_only_fields = ('id', 'updated_at', 'created_at',)
