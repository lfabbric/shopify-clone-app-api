from rest_framework import serializers
from core.models import Store


class StoreSerializer(serializers.ModelSerializer):
    """"Serialize a recipe"""

    class Meta:
        model = Store
        fields = (
            'id', 'title', 'logo'
        )
        read_only_fields = ('id', 'logo')


class StoreImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading the logo to the store"""

    class Meta:
        model = Store
        fields = ('id', 'logo')
        read_only_fields = ('id',)
