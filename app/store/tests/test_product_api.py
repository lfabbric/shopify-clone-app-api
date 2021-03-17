import os
import tempfile

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Store, Product, ProductType, ProductImage, \
                         ProductAttachment
from store import serializers


def image_upload_url(store):
    """return url for product images"""
    return reverse('store:productimage-list', args=[store])


def attachment_upload_url(store):
    """return url for product images"""
    return reverse('store:productattachment-list', args=[store])


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
        'stock': 3,
        'published': True
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

    def test_list_all_products(self):
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

    def test_list_products_by_tags(self):
        owner = sample_user()
        store1 = sample_store(owner)
        product1 = sample_product(owner, store1, title='Product A')
        product1.tags.add('fabric', 'disney')
        product2 = sample_product(owner, store1, title='Product B')
        product2.tags.add('fabric')
        product3 = sample_product(owner, store1, title='Product C')
        product3.tags.add('target')

        url = product_url(store1.slug)
        res = self.client.get(
            url,
            {'tags': 'fabric, disney'}
        )

        serializer = serializers.ProductSerializer(product1)
        serializer2 = serializers.ProductSerializer(product3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_get_products_with_type(self):
        owner = sample_user()
        store = sample_store(owner)
        product_type = ProductType.objects.create(
            name='Quilting Cotton',
            store=store,
            user=owner
        )
        product1 = sample_product(
            owner,
            store,
            title='Product A',
            type=product_type
        )

        url = detail_url(store.slug, product1.id)
        res = self.client.get(url)

        serializer = serializers.ProductSerializer(product1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class productImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@cinolabs.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)
        self.store = sample_store(user=self.user)
        self.product = sample_product(user=self.user, store=self.store)

    def tearDown(self):
        """Clean test files added"""
        self.product.get_images().delete()

    def test_upload_image_to_store(self):
        """Test upload an image"""
        url = image_upload_url(self.store.slug)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            payload = {
                'title': 'Main Product Image',
                'product': self.product.id,
                'is_primary': True,
                'image': ntf
            }
            res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('image', res.data)
        product_image = ProductImage.objects.get(pk=res.data['id'])
        self.assertTrue(os.path.exists(product_image.image.path))

        # test the the first image is saved as is_primary
        self.assertTrue(res.data['is_primary'])

        # upload second image - test that first is no longer primary
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            payload = {
                'title': 'Main Product Image 2',
                'product': self.product.id,
                'is_primary': True,
                'image': ntf
            }
            res = self.client.post(url, payload, format='multipart')

        product_image.refresh_from_db()
        product_image2 = ProductImage.objects.get(pk=res.data['id'])
        self.assertFalse(product_image.is_primary)
        self.assertTrue(product_image2.is_primary)

        # delete primary image and check if first image is back to is_primary
        product_image2.delete()
        product_image.refresh_from_db()
        self.assertTrue(product_image.is_primary)


class productAttachmentUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@cinolabs.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)
        self.store = sample_store(user=self.user)
        self.product = sample_product(user=self.user, store=self.store)

    def tearDown(self):
        """Clean test files added"""
        self.product.get_attachments().delete()

    def test_upload_attachment_to_store(self):
        url = attachment_upload_url(self.store.slug)
        with tempfile.NamedTemporaryFile(suffix='.txt') as ntf:
            ntf.write(b'Id,Title')
            ntf.seek(0)
            payload = {
                'title': 'Main Product Attachment',
                'product': self.product.id,
                'is_primary': False,
                'file': ntf
            }
            res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('file', res.data)
        product_attachment = ProductAttachment.objects.get(pk=res.data['id'])
        self.assertTrue(os.path.exists(product_attachment.file.path))

        # test the the first image is saved as is_primary
        self.assertTrue(res.data['is_primary'])
