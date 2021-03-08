from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Store, Product
from store import serializers


def product_url(slug):
    return reverse('store:product-list', args=[slug])


def detail_url(slug, id):
    return reverse('store:product-detail', args=[slug, id])


def detail_url_with_store(store, id):
    return reverse('store:product-detail', args=[id])


def sample_user(email='tmp_user@cinolabs.com', password='testpass'):
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
        'stock': 3
    }
    defaults.update(params)

    return Product.objects.create(
        user=user,
        store=store,
        **defaults
    )


class PublicProductApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_list_all_products_no_store(self):
        owner = sample_user()
        owner2 = sample_user(email='altnernate_user@cinolabs.com')
        store1 = sample_store(owner)
        store2 = sample_store(owner2, title='House of Nails')

        product1 = sample_product(owner, store1)
        sample_product(owner2, store2)

        url = product_url(store1.slug)
        res = self.client.get(url)
        serializer = serializers.ProductSerializer(product1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data)
