# Generated manually for loyalty system.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transaction", "0004_transaction_comment"),
        ("client", "0005_client_note_alter_client_public_phone_client_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="cashback_balance",
            field=models.FloatField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name="client",
            name="loyalty_tier",
            field=models.CharField(
                choices=[("bronze", "Bronze"), ("silver", "Silver"), ("gold", "Gold")],
                default="bronze",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="referral_code",
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="client",
            name="referred_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="referred_clients",
                to="client.client",
            ),
        ),
        migrations.AddField(
            model_name="client",
            name="total_spent_amount",
            field=models.FloatField(blank=True, default=0),
        ),
        migrations.CreateModel(
            name="CashbackEntry",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, editable=False)),
                ("entry_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "entry_type",
                    models.CharField(
                        choices=[
                            ("earned", "Earned"),
                            ("referral_bonus", "Referral bonus"),
                            ("adjustment", "Adjustment"),
                        ],
                        max_length=32,
                    ),
                ),
                ("amount", models.FloatField(default=0)),
                ("balance_after", models.FloatField(default=0)),
                ("note", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cashback_entries",
                        to="client.client",
                    ),
                ),
                (
                    "related_client",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="related_cashback_entries",
                        to="client.client",
                    ),
                ),
                (
                    "source_transaction",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="cashback_entry",
                        to="transaction.transaction",
                    ),
                ),
            ],
            options={
                "verbose_name": "Cashback entry",
                "verbose_name_plural": "Cashback entries",
                "ordering": ["-created_at", "-entry_id"],
            },
        ),
    ]
