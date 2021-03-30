from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Order, Store, OrderItem, Product

from decimal import Decimal


def order_url(store, revurl='commerce:order-list'):
    return reverse(revurl, args=[store])


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


def sample_order(user, store, **params):
    """create and return sample order"""
    defaults = {
        'amount': 15.15,
    }
    defaults.update(params)

    return Order.objects.create(
        user=user,
        store=store,
        **defaults
    )


def sample_orderitem(order, product, **params):
    defaults = {
        'quantity': 1,
        'price': product.price
    }
    defaults.update(params)

    return OrderItem.objects.create(
        order=order,
        product=product,
        **defaults
    )


class OrderTests(TestCase):
    """Test the store order (private)"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email='owner@cinolabs.com',
            password='testpass',
            name='store owner'
        )
        self.customer = get_user_model().objects.create_user(
            email='customer@cinolabs.com',
            password='testpass',
            name='Test Customer'
        )
        self.store = sample_store(self.owner)
        self.order = sample_order(self.customer, self.store)

        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)

    def test_order_save(self):
        """Test to show all orders made by the user"""
        product1 = sample_product(self.owner, self.store)
        product2 = sample_product(
            self.owner,
            self.store,
            title='Product 2',
            price=15.15
        )

        orderitem1 = sample_orderitem(
            self.order, product1
        )
        orderitem2 = sample_orderitem(
            self.order, product2, quantity=2
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.final_amount, Decimal('35.30'))

        self.assertEqual(orderitem1.total_price, Decimal('5.00'))
        self.assertEqual(orderitem2.total_price, Decimal('30.30'))


class PublicOrderApiTests(TestCase):
    """Basic test for authorization"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email='owner@cinolabs.com',
            password='testpass',
            name='store owner'
        )
        self.customer = get_user_model().objects.create_user(
            email='customer@cinolabs.com',
            password='testpass',
            name='Test Customer'
        )
        self.store = sample_store(self.owner)
        self.order = sample_order(self.customer, self.store)
        self.client = APIClient()

    def test_get_orders(self):
        url = order_url(self.store.slug)
        res = self.client.get(url)

        self.assertTrue(res.status_code, status.HTTP_401_UNAUTHORIZED)


class CustomerOrderApiTests(TestCase):
    """Test the store order (private)"""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email='owner@cinolabs.com',
            password='testpass',
            name='store owner'
        )
        self.customer = get_user_model().objects.create_user(
            email='customer@cinolabs.com',
            password='testpass',
            name='Test Customer'
        )
        self.store = sample_store(self.owner)
        self.order = sample_order(self.customer, self.store)
        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)

    def test_show_orders(self):
        """Test to show all orders made by the user"""
        url = order_url(self.store.slug)
        res = self.client.get(url)

        self.assertTrue(res.status_code, status.HTTP_200_OK)

    def test_print_order(self):
        """Test that printing an order works"""
        self.assertTrue(True)

    def test_show_order_detail(self):
        """Pull an order and show detail"""
        self.assertTrue(True)

    def test_update_order(self):
        """Update and order and watch it fail"""
        self.assertTrue(True)

    def test_update_order_detail(self):
        """Custommer adds notes to order - test notification"""
        self.assertTrue(True)


class StoreOwnerOrderApiTests(TestCase):
    """Test the store order from the perspective of the owner"""

    def test_show_all_orders(self):
        """Test to show all orders made by the user"""
        # Pagination required
        self.assertTrue(True)

    def test_print_order(self):
        """Test that printing an order works"""
        self.assertTrue(True)

    def test_show_order_detail(self):
        """Pull an order and show detail"""
        self.assertTrue(True)

    def test_update_order(self):
        """Update and order and watch it work"""
        self.assertTrue(True)

    def test_update_order_detail(self):
        """Owner adds notes to order - test notification"""
        self.assertTrue(True)
