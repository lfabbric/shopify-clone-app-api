# Generated by Django 3.1.7 on 2021-03-24 19:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_shipping'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.PositiveIntegerField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing Payment'), ('PACKAGED', 'Ready to be shipped'), ('SHIPPED', 'In Mail'), ('RECEIVED', 'Shipment Received'), ('CLOSED', 'Closed')], db_index=True, default='PROCESSING', verbose_name='status')),
                ('currency', models.CharField(default='CAD', max_length=3, verbose_name='Currency')),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('final_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('is_paid', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('finished_at', models.DateTimeField(blank=True, verbose_name='Finalized')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.store')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=20),
        ),
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.PositiveIntegerField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing Payment'), ('PACKAGED', 'Ready to be shipped'), ('SHIPPED', 'In Mail'), ('RECEIVED', 'Shipment Received'), ('CLOSED', 'Closed')], default='PROCESSING', verbose_name='status')),
                ('customer_notified', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, verbose_name='description')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.order')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=2, max_digits=20)),
                ('discount_price', models.DecimalField(decimal_places=2, max_digits=20)),
                ('final_price', models.DecimalField(decimal_places=2, max_digits=20)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=20)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.product')),
            ],
            options={
                'unique_together': {('order', 'product')},
            },
        ),
    ]