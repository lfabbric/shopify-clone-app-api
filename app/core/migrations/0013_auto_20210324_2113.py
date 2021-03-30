# Generated by Django 3.1.7 on 2021-03-24 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20210324_1906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing Payment'), ('PACKAGED', 'Ready to be shipped'), ('SHIPPED', 'In Mail'), ('RECEIVED', 'Shipment Received'), ('CLOSED', 'Closed')], db_index=True, default='PROCESSING', max_length=25, verbose_name='status'),
        ),
        migrations.AlterField(
            model_name='orderstatushistory',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing Payment'), ('PACKAGED', 'Ready to be shipped'), ('SHIPPED', 'In Mail'), ('RECEIVED', 'Shipment Received'), ('CLOSED', 'Closed')], default='PROCESSING', max_length=25, verbose_name='status'),
        ),
    ]