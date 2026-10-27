from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0003_order_delivery_agent_name_order_delivery_agent_phone")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="mpesa_checkout_request_id",
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name="order",
            name="mpesa_merchant_request_id",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="order",
            name="mpesa_account_reference",
            field=models.CharField(blank=True, max_length=12),
        ),
    ]
