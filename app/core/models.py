import uuid
import operator

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
                                        PermissionsMixin
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

from phonenumber_field.modelfields import PhoneNumberField
from taggit.managers import TaggableManager
from functools import reduce
from decimal import Decimal, ROUND_HALF_UP


def return_date_time(days=10):
    now = timezone.now()
    return now + timezone.timedelta(days=days)


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
        store=instance.store.uuid,
        file=filename
    )


def upload_path_handler(instance, filename):
    """Generate file path for an uploaded image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return "uploads/{store}/product/{product}/{file}".format(
        store=instance.product.store.uuid,
        product=instance.product.slug,
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


class ProductManager(models.Manager):

    def active(self):
        return self.filter(published=True)

    def in_stock(self):
        return self.active().filter(stock__gte=1)


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
    price = models.DecimalField(decimal_places=2, max_digits=20)
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

    objects = models.Manager()
    broswer = ProductManager()

    class Meta:
        unique_together = ('slug', 'store',)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Product, self).save(*args, **kwargs)

    def get_images(self):
        images = ProductImage.objects.filter(
            product__id=self.id
        )
        return images

    def get_attachments(self):
        attachments = ProductAttachment.objects.filter(
            product__id=self.id
        )
        return attachments

    def get_reviews(self, is_active=True):
        reviews = ProductReview.objects.filter(
            product__id=self.id
        )
        return reviews


class ProductImage(models.Model):
    title = models.CharField(_("Title"), max_length=32, blank=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(_("Image"), upload_to=upload_path_handler)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}_{}({})'.format(
            self.product.title,
            self.title,
            self.is_primary
        )


class ProductAttachment(models.Model):
    title = models.CharField(_("Title"), max_length=32, blank=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    file = models.FileField(_("File"), upload_to=upload_path_handler)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.product.title, self.title)


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    rating = models.PositiveIntegerField(
        _('rating'),
        default=1,
        validators=[
            MaxValueValidator(5),
            MinValueValidator(1)
        ]
    )
    title = models.CharField(_("Title"), max_length=32, blank=False)
    review = models.TextField(_('Description'), blank=False)
    was_helpful = models.IntegerField(_('Helpful'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.product.title, self.title)


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


class Shipping(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )
    company = models.CharField(_("Company"), max_length=32, blank=True)
    address = models.CharField(_("Address"), max_length=64, blank=False)
    suite = models.CharField(
        _("Appartment, suite, etc"),
        max_length=64,
        blank=True
    )
    postal_code = models.CharField(
        _("Postal Code"),
        max_length=10,
        blank=False
    )
    city = models.ForeignKey(
        to='cities_light.City',
        blank=False,
        related_name='city',
        on_delete=models.CASCADE
    )
    state = models.ForeignKey(
        to='cities_light.Region',
        blank=False,
        related_name='state',
        on_delete=models.CASCADE
    )
    country = models.ForeignKey(
        to='cities_light.Country',
        blank=False,
        related_name='country',
        on_delete=models.CASCADE
    )
    telephone = PhoneNumberField(_("Phone Number"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {} {}'.format(
            self.user.name,
            self.address,
            self.city
        )

    class Meta:
        ordering = ['-updated_at', ]


# GuestShipping(Shipping)
# user blank but use Cart.uuid as ref
# guest email
# foreignkey to order


class Order(models.Model):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    PACKAGED = 'PACKAGED'
    SHIPPED = 'SHIPPED'
    RECEIVED = 'RECEIVED'
    CLOSED = 'CLOSED'

    STATUS_CHOICES = (
        (PENDING, _('Pending')),
        (PROCESSING, _('Processing Payment')),
        (PACKAGED, _('Ready to be shipped')),
        (SHIPPED, _('In Mail')),
        (RECEIVED, _('Shipment Received')),
        (CLOSED, _('Closed')),
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    status = models.CharField(
        _('status'),
        choices=STATUS_CHOICES,
        db_index=True,
        max_length=25,
        default=PROCESSING
    )
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        blank=False,
        default="CAD"
    )
    amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=20
    )
    discount_amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=20
    )
    final_amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=20
    )
    is_paid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(_("Finalized"), null=True)

    objects = models.Manager()
    # browser = OrderManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.store}_{self.user.name}: {self.amount}/{self.currency}'

    def save(self, *args, **kwargs):
        cents = Decimal('0.01')
        order_items = self.order_items.all()
        self.amount = order_items.aggregate(
            Sum('total_price')
        )['total_price__sum'] if order_items.exists() else 0.00
        self.final_amount = Decimal(self.amount)-Decimal(self.discount_amount)
        self.final_amount = Decimal(self.final_amount).quantize(
            cents,
            ROUND_HALF_UP
        )
        super(Order, self).save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.CharField(
        _('status'),
        max_length=25,
        choices=Order.STATUS_CHOICES,
        default=Order.PROCESSING
    )
    customer_notified = models.BooleanField(default=False)
    notes = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    discount_price = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00
    )
    final_price = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00
    )
    total_price = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00
    )

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f'{self.order.id}: {self.total_price}'

    def save(self,  *args, **kwargs):
        cents = Decimal('0.01')
        self.final_price = \
            self.discount_price if self.discount_price > 0 else self.price
        self.total_price = Decimal(self.quantity) * Decimal(self.final_price)
        self.total_price = Decimal(self.total_price).quantize(
            cents,
            ROUND_HALF_UP
        )
        super(OrderItem, self).save(*args, **kwargs)
        self.order.save()


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        blank=False,
        default="CAD"
    )
    amount = models.DecimalField(
        default=0.00,
        decimal_places=2,
        max_digits=20
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invalid_at = models.DateTimeField(_("Invalid"), default=return_date_time())

    def __str__(self):
        return f'{self.id}: {self.amount}/{self.currency}'

    def save(self, *args, **kwargs):
        cents = Decimal('0.01')
        cart_items = self.cart_items.all()
        self.amount = cart_items.aggregate(
            Sum('total_price')
        )['total_price__sum'] if cart_items.exists() else 0.00
        self.amount = Decimal(self.amount).quantize(
            cents,
            ROUND_HALF_UP
        )
        super(Cart, self).save(*args, **kwargs)

    def add(self, product, quantity=1, note=""):
        """Add or increment product to cart"""
        item, created = self.cart_items.get_or_create(
            product=product,
            defaults={'quantity': quantity, 'note': note}
        )
        if not created:
            item.quantity += quantity
            item.save()

    def remove(self, product):
        self.cart_items.filter(
            product=product
        ).delete()


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    note = models.TextField(_('Note'))
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00
    )
    discount_price = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00
    )
    final_price = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00
    )
    total_price = models.DecimalField(
        decimal_places=2,
        max_digits=20,
        default=0.00
    )

    def __str__(self):
        return f'{self.cart_id} - {self.product.title}: {self.price}'

    class Meta:
        unique_together = ('cart', 'product')

    def save(self,  *args, **kwargs):
        cents = Decimal('0.01')
        if not self.product.price:
            p = Product.objects.get(id=self.product.id)
            self.price = p.price
        else:
            self.price = self.product.price

        self.final_price = \
            self.discount_price if self.discount_price > 0 else self.price
        self.total_price = Decimal(self.quantity) * Decimal(self.final_price)
        self.total_price = Decimal(self.total_price).quantize(
            cents,
            ROUND_HALF_UP
        )
        super(CartItem, self).save(*args, **kwargs)
        self.cart.save()
