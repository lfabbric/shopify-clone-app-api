from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Store, Product


def get_cart_url(store, revurl='commerce:cart-list'):
    return reverse(revurl, args=[store])


def cart_detail_url(store, cart_id, revurl='commerce:cart-detail'):
    return reverse(revurl, args=[store, cart_id])


def sample_user(email='tmp_user@cinolabs.com', password='testpass'):
    return get_user_model().objects.create_user(email, password)


def sample_store(user, title='Main Store', slug='main_store'):
    return Store.objects.create(
        user=user,
        title=title,
        slug=slug
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


class GuestCartApiTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email='owner@cinolabs.com',
            password='testpass',
            name='store owner'
        )
        self.store = sample_store(self.owner)
        self.product1 = sample_product(self.owner, self.store)
        self.product2 = sample_product(
            self.owner,
            self.store,
            title='Product 2',
            price=15.15
        )
        self.client = APIClient()

    def test_get_cartlist(self):
        url = get_cart_url(self.store.slug)
        res = self.client.get(url)
        self.assertTrue(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_cart(self):
        url = get_cart_url(self.store.slug)
        res = self.client.post(url)
        self.assertTrue(res.status_code, status.HTTP_201_CREATED)

    def test_add_product(self):
        url = get_cart_url(self.store.slug)
        res = self.client.post(url)
        cart_id = res.data['id']
        url = cart_detail_url(
            self.store.slug, cart_id, 'commerce:cart-add-to-cart'
        )
        payload = {
            'product_id': self.product1.id
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user'], None)
        self.assertEqual(res.data['amount'], '5.00')

        payload = {
            'product_id': self.product1.id
        }

        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user'], None)
        self.assertEqual(res.data['amount'], '10.00')

        payload = {
            'product_id': self.product1.id,
            'quantity': 2
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user'], None)
        self.assertEqual(res.data['amount'], '20.00')

    def test_delete_product(self):
        url = get_cart_url(self.store.slug)
        res = self.client.post(url)
        cart_id = res.data['id']
        url = cart_detail_url(
            self.store.slug,
            cart_id,
            'commerce:cart-add-to-cart'
        )
        payload = {
            'product_id': self.product1.id
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user'], None)
        self.assertEqual(res.data['amount'], '5.00')

        url = cart_detail_url(
            self.store.slug,
            cart_id,
            'commerce:cart-remove-from-cart'
        )
        payload = {
            'product_id': self.product1.id
        }

        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['cart_items']), 0)


class AuthenticatedCartApiTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email='owner@cinolabs.com',
            password='testpass',
            name='store owner'
        )
        self.store = sample_store(self.owner)
        self.product1 = sample_product(self.owner, self.store)
        self.product2 = sample_product(
            self.owner,
            self.store,
            title='Product 2',
            price=15.15
        )
        self.client = APIClient()
        self.customer = get_user_model().objects.create_user(
            email='customer@cinolabs.com',
            password='testpass',
            name='Just A Customer'
        )
        self.client.force_authenticate(user=self.customer)

    def test_add_product(self):
        url = get_cart_url(self.store.slug)
        res = self.client.post(url)
        cart_id = res.data['id']
        url = cart_detail_url(
            self.store.slug,
            cart_id,
            'commerce:cart-add-to-cart'
        )
        payload = {
            'product_id': self.product1.id
        }
        res = self.client.post(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user']['email'], self.customer.email)
        self.assertEqual(res.data['amount'], '5.00')
