from django.utils import timezone
from django.core.management.base import BaseCommand

from core.models import Cart


class Command(BaseCommand):
    """Django command to inactivate or delete cart items"""

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete carts that are no longer active',
        )

    def handle(self, *args, **options):
        if options['delete']:
            carts = Cart.objects.filter(
                is_active=False
            ).delete()
            self.stdout.write(self.style.SUCCESS(f'Deleting {carts[0]} items'))
        else:
            carts = Cart.objects.filter(
                invalid_at__lte=timezone.now()
            ).update(is_active=False)
            self.stdout.write(self.style.SUCCESS(f'Updating {carts} items'))

        self.stdout.write(self.style.SUCCESS('Cart cleanup complete'))
