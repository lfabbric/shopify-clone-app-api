import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                        PermissionsMixin
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.text import slugify

from taggit.managers import TaggableManager


def store_image_file_path(instance, filename):
    """Generate file path for an uploaded image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return "uploads/{store}/{file}".format(
        store=instance.uuid,
        file=filename
    )


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Overload the create user method, use email as id"""
        if not email:
            raise ValueError('Email address is required')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self.db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports email instead of username"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Store(models.Model):
    title = models.CharField(_("title"), max_length=35)
    slug = models.SlugField(max_length=40, unique=True, blank=False)
    is_active = models.BooleanField(default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    logo = models.ImageField(blank=True, upload_to=store_image_file_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Store, self).save(*args, **kwargs)

    def __str__(self):
        return '{}'.format(self.title)


class ProductType(models.Model):
    name = models.CharField(_("name"), max_length=35)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title


class Product(models.Model):

    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
    FULFILLMENT_CHOICES = (
        (MANUAL, _("Manual")),
        (AUTOMATIC, _("Automatic")),
    )

    title = models.CharField(_("title"), max_length=35)
    slug = models.SlugField(max_length=40, blank=False)
    body = models.TextField(_('body'))
    price = models.DecimalField(decimal_places=2, max_digits=8)
    taxable = models.BooleanField(default=True)
    tags = TaggableManager()
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    purchased = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField()
    length = models.FloatField(_("Length"), default=.5)
    fulfillment = models.CharField(
        _('Fulfillment Service'),
        max_length=9,
        choices=FULFILLMENT_CHOICES,
        default=MANUAL
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    type = models.ForeignKey(
        ProductType,
        null=True,
        on_delete=models.SET_NULL
    )

    published = models.BooleanField(default=False)
    date_available = models.DateTimeField(
        _("Available"),
        auto_now_add=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('slug', 'store',)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Product, self).save(*args, **kwargs)
