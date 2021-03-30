from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Shipping, Store
from cities_light.models import City, Region, Country


def shipping_url(store, revurl='commerce:shipping-list'):
    return reverse(revurl, args=[store])


def sample_shipping(user, store, **params):
    """create and return sample shipping address"""
    defaults = {
        'address': '123 Sample Address',
        'postal_code': 'A1B 2C3',
        'city': City.objects.get(name='Calgary'),
        'state': Region.objects.get(name='Alberta'),
        'country': Country.objects.get(name='Canada')
    }
    defaults.update(params)

    return Shipping.objects.create(
        user=user,
        store=store,
        **defaults
    )


def sample_user(email='tmp_user@cinolabs.com', password='testpass'):
    return get_user_model().objects.create_user(email, password)


def sample_store(user, title='Main Store', slug='main_store'):
    return Store.objects.create(
        user=user,
        title=title,
        slug=slug
    )


class PrivateShippingApiTests(TestCase):
    """Test the store api (private)"""

    def setUp(self):
        self.country = Country(name="Canada", tld="ca")
        self.country.save()
        self.region = Region(
            name="Alberta",
            country=self.country
        )
        self.region.save()
        self.city = City(
            name='Calgary',
            region=self.region,
            country=self.country
        )
        self.city.save()

        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@cinolabs.com',
            password='testpass',
            name='name'
        )
        self.store = sample_store(self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_latest_shipping(self):
        customer = get_user_model().objects.create_user(
            email='customer@cinolabs.com',
            password='testpass',
            name='Test Customer'
        )
        shipping1 = sample_shipping(customer, self.store)
        shipping2 = sample_shipping(
            customer,
            self.store,
            address="999 Some Other Address"
        )

        url = shipping_url(self.store.slug)
        res = self.client.get(url, {'userid': customer.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        url = shipping_url(
            self.store.slug,
            revurl='commerce:shipping-get-active'
        )
        res = self.client.get(url, {'userid': customer.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['address'], shipping2.address)

        shipping1.address = "1234 updated address"
        shipping1.save()
        url = shipping_url(
            self.store.slug,
            revurl='commerce:shipping-get-active'
        )
        res = self.client.get(url, {'userid': customer.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['address'], shipping1.address)
