# Generated by Django 5.2.4 on 2025-07-07 23:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookkeeping', '0004_alter_invoiceitem_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoiceNumberTracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_number', models.PositiveIntegerField(default=1)),
            ],
        ),
    ]
