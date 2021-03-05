import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Store
from store import serializers


STORE_URL = reverse('store:store-list')


def image_upload_url(store_id):
    """return url for store logo"""
    return reverse('store:store-upload-image', args=[store_id])


def sample_user(email='tmp_user@cinolabs.com', password='testpass'):
    return get_user_model().objects.create_user(email, password)


def sample_store(user, title='Main Store'):
    return Store.objects.create(user=user, title=title)


def detail_url(id):
    return reverse('store:store-detail', args=[id])


class PublicUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_list_stores(self):
        sample_store(sample_user())
        res = self.client.get(STORE_URL)
        stores = Store.objects.all().order_by('-id')
        serializer = serializers.StoreSerializer(stores, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_store_detail(self):
        store = sample_store(sample_user())
        res = self.client.get(detail_url(store.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)


class PrivateUserApiTests(TestCase):
    """Test the store api (private)"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@cinolabs.com',
            password='testpass',
            name='name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_basic_store(self):
        """Test creating a user that already exists"""
        payload = {
            'title': 'Test store name'
        }

        self.client.post(STORE_URL, payload)

        exists = Store.objects.filter(
            user=self.user,
            title=payload['title']
        ).exists()

        self.assertTrue(exists)

    def test_edit_another_users_store(self):
        store = sample_store(sample_user())
        url = detail_url(store.id)
        payload = {
            'title': 'Revised Title'
        }

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class StoreImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@cinolabs.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)
        self.store = sample_store(user=self.user)

    def tearDown(self):
        """Clean test files added"""
        self.store.logo.delete()

    def test_upload_image_to_store(self):
        """Test upload an image"""
        url = image_upload_url(self.store.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'logo': ntf}, format='multipart')

        self.store.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('logo', res.data)
        self.assertTrue(os.path.exists(self.store.logo.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.store.id)
        res = self.client.post(url, {'logo': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
