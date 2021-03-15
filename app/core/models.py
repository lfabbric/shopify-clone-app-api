import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                        PermissionsMixin
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.db.models import Q
from django.utils import timezone

from taggit.managers import TaggableManager
import operator
from functools import reduce


def store_image_file_path(instance, filename):
    """Generate file path for an uploaded image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return "uploads/{store}/{file}".format(
        store=instance.uuid,
        file=filename
    )


def collection_image_file_path(instance, filename):
    """Generate file path for an uploaded image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return "uploads/{store}/collection/{file}".format(
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


class Collection(models.Model):
    ALL = Q.AND
    ANY = Q.OR
    CONDITION_MATCH_CHOICES = (
        (ALL, _("All conditions")),
        (ANY, _("Any conditions")),
    )

    title = models.CharField(_("title"), max_length=35)
    slug = models.SlugField(max_length=100, blank=False)
    body = models.TextField(_('body'))
    image = models.ImageField(blank=True, upload_to=collection_image_file_path)
    type = models.CharField(
        _('Collection Type'),
        max_length=9,
        choices=CONDITION_MATCH_CHOICES,
        default=ALL
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def operator_type(self):
        if self.type == self.ANY:
            return operator.or_
        return operator.and_

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Collection, self).save(*args, **kwargs)

    def get_products(self):
        conditions = Condition.objects.prefetch_related('collection').filter(
            collection__id=self.id
        ).order_by('field_reference')

        products = Product.objects.all().filter(
            store__slug=self.store.slug,
            published=True,
            date_available__lte=timezone.now()
        )
        prev = None
        nquery = []
        nquery2 = []
        for c in conditions:
            choice = next(
                item for item in Condition._CHOICES
                if item["key"] == c.field_reference
            )
            if choice:
                dynamic_filter = {
                    f"{choice['field']}"
                    f"{choice['choices'][c.filter_type]['match']}": c.field_val
                }
                if prev and prev != c.field_reference:
                    nquery2.append(
                        (reduce(operator.or_, nquery))
                    )
                    nquery = []
                if choice['choices'][c.filter_type]['negation']:
                    q = ~Q(**dynamic_filter)
                else:
                    q = Q(**dynamic_filter)
                nquery.append(q)
            prev = c.field_reference

        nquery2.append(
            (reduce(operator.or_, nquery))
        )

        query = (reduce(self.operator_type(), nquery2))
        products = products.filter(query)
        products = products.distinct()

        return products

    def __str__(self):
        return '{}'.format(self.title)


class Condition(models.Model):
    EQUAL = "EQUAL"
    NOTEQUAL = "NOTEQUAL"
    GTE = "GREATERTHANEQUAL"
    LTE = "LESSTHANEQUAL"
    STARTSWITH = "STARTSWITH"
    ENDSWITH = "ENDSWITH"
    CONTAINS = "CONTAINS"
    NOTCONTAIN = "NOTCONTAIN"

    FILTER_CHOICES = (
        (EQUAL, _("Is equal to")),
        (NOTEQUAL, _("Not equal to")),
        (GTE, _("Greater than")),
        (LTE, _("Less than")),
        (STARTSWITH, _("Starts with")),
        (ENDSWITH, _("Ends with")),
        (CONTAINS, _("Contains")),
        (NOTCONTAIN, _("Does not contain")),
    )

    PRODUCT_TYPE = "TYPE"
    PRODUCT_TITLE = "TITLE"
    PRODUCT_TAG = "TAG"
    PRODUCT_STOCK = "STOCK"
    PRODUCT_PRICE = "PRICE"

    _default_choices = {
        EQUAL: {'match': '__iexact', 'negation': False},
        NOTEQUAL: {'match': '__iexact', 'negation': True},
        STARTSWITH: {'match': '__istartswith', 'negation': False},
        ENDSWITH: {'match': '__iendswith', 'negation': False},
        CONTAINS: {'match': '__contains', 'negation': False},
        NOTCONTAIN: {'match': '__contains', 'negation': True},
    }

    _numeric_choices = {
        EQUAL: {'match': '__iexact', 'negation': False},
        NOTEQUAL: {'match': '__iexact', 'negation': True},
        GTE: {'match': '__gte', 'negation': False},
        LTE: {'match': '__lte', 'negation': False},
    }

    _CHOICES = [
        {
            'key': PRODUCT_TYPE,
            'label': _("Product Type"),
            'choices': _default_choices,
            'field': 'type__name',
        },
        {
            'key': PRODUCT_TITLE,
            'label': _("Product Title"),
            'choices': _default_choices,
            'field': PRODUCT_TITLE.lower(),
        },
        {
            'key': PRODUCT_TAG,
            'label': _("Product Tag"),
            'choices': _default_choices,
            'field': 'tags__name',
        },
        {
            'key': PRODUCT_STOCK,
            'label': _("Product Stock"),
            'choices': _numeric_choices,
            'field': PRODUCT_STOCK.lower(),
        },
        {
            'key': PRODUCT_PRICE,
            'label': _("Product Price"),
            'choices': _numeric_choices,
            'field': PRODUCT_PRICE.lower(),
        },
    ]
    FIELD_REF_CHOICES = tuple([
        (v['key'], v['label']) for i, v in enumerate(_CHOICES)
    ])

    field_reference = models.CharField(
        _('Field Reference'),
        max_length=25,
        choices=FIELD_REF_CHOICES,
        default=PRODUCT_TYPE
    )
    filter_type = models.CharField(
        _('Filter Type'),
        max_length=25,
        choices=FILTER_CHOICES,
        default=EQUAL
    )
    field_val = models.CharField(_("Condition Value"), max_length=35)
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return '{} {} {}'.format(
            dict(self.FIELD_REF_CHOICES)[self.field_reference],
            dict(self.FILTER_CHOICES)[self.filter_type],
            self.field_val
        )
