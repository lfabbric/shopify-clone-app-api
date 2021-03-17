# post_save and post_delete
from core import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Count, Q


@receiver(post_save, sender=models.ProductImage)
def update_primary(sender, instance, created, **kwargs):
    if instance.is_primary:
        models.ProductImage.objects.filter(
            product__id=instance.product.id,
            is_primary=True
        ).exclude(
            id=instance.id
        ).update(
            is_primary=False
        )
    else:
        alternate_primary = models.ProductImage.objects.filter(
            product__id=instance.product.id,
            is_primary=True
        ).exclude(
            id=instance.id
        ).count()
        if not alternate_primary:
            instance.is_primary = True
            post_save.disconnect(update_primary, sender=models.ProductImage)
            instance.save()
            post_save.connect(update_primary, sender=models.ProductImage)


@receiver(post_delete, sender=models.ProductImage)
def update_alternative_is_primary(sender, instance, **kwargs):
    q = models.ProductImage.objects.filter(
        product__id=instance.product.id
    ).annotate(
        total=Count('id', distinct=True)
    ).annotate(
        primary=Count('is_primary', filter=Q(is_primary=True), distinct=True)
    )
    if q and q[0].total and not q[0].primary:
        post_save.disconnect(update_primary, sender=models.ProductImage)
        pi = models.ProductImage.objects.filter(
            product__id=instance.product.id
        )[:1].get()
        pi.is_primary = True
        pi.save()
        post_save.connect(update_primary, sender=models.ProductImage)


@receiver(post_save, sender=models.ProductAttachment)
def update_primary_attachment(sender, instance, created, **kwargs):
    if instance.is_primary:
        models.ProductAttachment.objects.filter(
            product__id=instance.product.id,
            is_primary=True
        ).exclude(
            id=instance.id
        ).update(
            is_primary=False
        )
    else:
        alternate_primary = models.ProductAttachment.objects.filter(
            product__id=instance.product.id,
            is_primary=True
        ).exclude(
            id=instance.id
        ).count()
        if not alternate_primary:
            instance.is_primary = True
            post_save.disconnect(
                update_primary_attachment, sender=models.ProductAttachment
            )
            instance.save()
            post_save.connect(
                update_primary_attachment, sender=models.ProductAttachment
            )


@receiver(post_delete, sender=models.ProductAttachment)
def update_alternative_attachment_is_primary(sender, instance, **kwargs):
    q = models.ProductAttachment.objects.filter(
        product__id=instance.product.id
    ).annotate(
        total=Count('id', distinct=True)
    ).annotate(
        primary=Count('is_primary', filter=Q(is_primary=True), distinct=True)
    )
    if q and q[0].total and not q[0].primary:
        post_save.disconnect(
            update_primary_attachment, sender=models.ProductAttachment
        )
        pi = models.ProductAttachment.objects.filter(
            product__id=instance.product.id
        )[:1].get()
        pi.is_primary = True
        pi.save()
        post_save.connect(
            update_primary_attachment, sender=models.ProductAttachment
        )
