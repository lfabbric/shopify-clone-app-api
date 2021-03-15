from rest_framework import serializers
from core.models import Store, Product, ProductType, Collection


class StringListField(serializers.ListField):
    child = serializers.CharField()

    def to_representation(self, data):
        return ' '.join(data.values_list('name', flat=True))


class StoreSerializer(serializers.ModelSerializer):
    """"Serialize a recipe"""

    class Meta:
        model = Store
        lookup_field = 'slug'
        # extra_kwargs = {'url': {'lookup_field':'slug'}}

        fields = (
            'title', 'logo', 'slug',
        )
        read_only_fields = ('id', 'logo',)


class StoreImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading the logo to the store"""

    class Meta:
        model = Store
        fields = ('id', 'logo',)
        read_only_fields = ('id',)


class ProductTypeSerializer(serializers.ModelSerializer):
    """Serializer for uploading the logo to the store"""

    class Meta:
        model = ProductType
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    type = ProductTypeSerializer()
    tags = StringListField()

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'body', 'store', 'fulfillment', 'taxable',
            'price', 'stock', 'length', 'purchased', 'tags', 'type'
        )
        read_only_fields = ('id',)


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for uploading the logo to the store"""

    class Meta:
        model = Collection
        fields = ('id', 'title', 'type', 'image')
        read_only_fields = ('id',)
