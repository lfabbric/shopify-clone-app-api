from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Store, Product, Collection, Condition, ProductType
from store import serializers


def collection_url(slug):
    return reverse('store:collection-list', args=[slug])


def product_by_collection_url(slug, id):
    return reverse('store:collection-product-list', args=[slug, id])


def sample_user(email='admin@cinolabs.com', password='testpass'):
    return get_user_model().objects.create_user(email, password)


def sample_store(user, title='Main Store'):
    return Store.objects.create(
        user=user,
        title=title
    )


def sample_product(user, store, **params):
    """create and return sample product"""
    defaults = {
        'title': 'Sample Product',
        'price': 5.00,
        'stock': 3,
        'published': True
    }
    defaults.update(params)

    return Product.objects.create(
        user=user,
        store=store,
        **defaults
    )


def sample_collection(user, store, **params):
    defaults = {
        'title': 'My Collection',
        'type': Collection.ALL,
    }
    defaults.update(params)

    return Collection.objects.create(
        user=user,
        store=store,
        **defaults
    )


def sample_condition(collection, **params):
    defaults = {
        'field_reference': Condition.PRODUCT_TAG,
        'filter_type': Condition.EQUAL,
        'field_val': 'Disney'
    }
    defaults.update(params)

    return Condition.objects.create(
        collection=collection,
        **defaults
    )


class PublicCollectionApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_list_collections(self):
        owner = sample_user()
        store = sample_store(owner)
        collection = sample_collection(owner, store)

        url = collection_url(store.slug)
        res = self.client.get(url)
        serializer = serializers.CollectionSerializer(collection)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data)

    def test_get_products_by_collection_any(self):
        owner = sample_user()
        store = sample_store(owner)
        collection = sample_collection(owner, store, type=Collection.ANY)
        sample_condition(collection, field_val='Disney')
        sample_condition(collection, field_val='TsumTsum')
        product1 = sample_product(owner, store, title='Product A')
        product1.tags.add('TsumTsum', 'disney')
        product2 = sample_product(owner, store, title='Product B')
        product2.tags.add('TsumTsum')
        product3 = sample_product(owner, store, title='Product C')
        product3.tags.add('Should Not Be here')

        url = product_by_collection_url(store.slug, collection.id)
        res = self.client.get(
            url
        )

        serializer_in1 = serializers.ProductSerializer(product1)
        serializer_in2 = serializers.ProductSerializer(product2)
        serializer_notin1 = serializers.ProductSerializer(product3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_in1.data, res.data)
        self.assertIn(serializer_in2.data, res.data)
        self.assertNotIn(serializer_notin1.data, res.data)

    def test_get_products_by_collection_all(self):
        owner = sample_user()
        store = sample_store(owner)
        collection = sample_collection(owner, store, type=Collection.ALL)
        sample_condition(collection, field_val='Disney')
        sample_condition(collection, field_val='TsumTsum')
        product1 = sample_product(owner, store, title="Product A")
        product1.tags.add("Disney", "TsumTsum")
        product2 = sample_product(owner, store, title="Product B")
        product2.tags.add("Disney")
        product3 = sample_product(owner, store, title="Product C")
        product3.tags.add("green")

        url = product_by_collection_url(store.slug, collection.id)
        res = self.client.get(
            url
        )

        serializer_in1 = serializers.ProductSerializer(product1)
        serializer_in2 = serializers.ProductSerializer(product2)
        serializer_notin1 = serializers.ProductSerializer(product3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_in1.data, res.data)
        self.assertIn(serializer_in2.data, res.data)
        self.assertNotIn(serializer_notin1.data, res.data)

    def test_get_products_by_collection_type(self):
        owner = sample_user()
        store = sample_store(owner)
        collection = sample_collection(owner, store, type=Collection.ANY)
        pt = ProductType.objects.create(
            name='Quilting Cotton',
            store=store,
            user=owner
        )
        pt2 = ProductType.objects.create(
            name='Zippers',
            store=store,
            user=owner
        )
        pt3 = ProductType.objects.create(
            name='Thread',
            store=store,
            user=owner
        )
        product1 = sample_product(owner, store, title="Product A", type=pt)
        product2 = sample_product(owner, store, title="Product B", type=pt2)
        product3 = sample_product(owner, store, title="Product C", type=pt3)

        sample_condition(
            collection,
            field_val=pt.name,
            field_reference=Condition.PRODUCT_TYPE
        )
        sample_condition(
            collection,
            field_val=pt2.name,
            field_reference=Condition.PRODUCT_TYPE
        )

        url = product_by_collection_url(store.slug, collection.id)
        res = self.client.get(
            url
        )

        serializer_in1 = serializers.ProductSerializer(product1)
        serializer_in2 = serializers.ProductSerializer(product2)
        serializer_notin2 = serializers.ProductSerializer(product3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_in1.data, res.data)
        self.assertIn(serializer_in2.data, res.data)
        self.assertNotIn(serializer_notin2.data, res.data)

        collection.type = Collection.ALL
        collection.save()
        collection.refresh_from_db()

        res = self.client.get(
            url
        )

        serializer_in1 = serializers.ProductSerializer(product1)
        serializer_in2 = serializers.ProductSerializer(product2)
        serializer_notin2 = serializers.ProductSerializer(product3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_in1.data, res.data)
        self.assertIn(serializer_in2.data, res.data)
        self.assertNotIn(serializer_notin2.data, res.data)

    def test_get_products_by_collection_complex(self):
        owner = sample_user()
        store = sample_store(owner)
        collection = sample_collection(owner, store, type=Collection.ALL)
        pt = ProductType.objects.create(
            name='Quilting Cotton',
            store=store,
            user=owner
        )
        pt2 = ProductType.objects.create(
            name='Zippers',
            store=store,
            user=owner
        )
        pt3 = ProductType.objects.create(
            name='Thread',
            store=store,
            user=owner
        )
        product1 = sample_product(
            owner,
            store,
            title="Product A",
            type=pt
        )
        product1.tags.add("Disney", "TsumTsum")
        product2 = sample_product(
            owner,
            store,
            title="Product B",
            type=pt2
        )
        product3 = sample_product(
            owner,
            store,
            title="Product C",
            type=pt3
        )
        sample_condition(
            collection,
            field_val=pt.name,
            field_reference=Condition.PRODUCT_TYPE
        )
        sample_condition(
            collection,
            field_val=pt2.name,
            field_reference=Condition.PRODUCT_TYPE
        )
        sample_condition(collection, field_val='Disney')
        url = product_by_collection_url(store.slug, collection.id)
        res = self.client.get(
            url
        )

        serializer1 = serializers.ProductSerializer(product1)
        serializer2 = serializers.ProductSerializer(product2)
        serializer3 = serializers.ProductSerializer(product3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

        collection.type = Collection.ANY
        collection.save()
        collection.refresh_from_db()

        res = self.client.get(
            url
        )

        serializer1 = serializers.ProductSerializer(product1)
        serializer2 = serializers.ProductSerializer(product2)
        serializer3 = serializers.ProductSerializer(product3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
