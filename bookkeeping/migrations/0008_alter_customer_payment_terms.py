# Generated by Django 5.2.4 on 2025-07-08 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookkeeping', '0007_invoice_enable_finance_charge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='payment_terms',
            field=models.CharField(choices=[('net_15', 'Net 15'), ('net_30', 'Net 30'), ('net_60', 'Net 60'), ('net_90', 'Net 90'), ('due_on_receipt', 'Due on Receipt')], max_length=20),
        ),
    ]
