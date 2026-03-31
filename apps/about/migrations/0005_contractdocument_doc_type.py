from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("about", "0004_contractdocument"),
    ]

    operations = [
        migrations.AddField(
            model_name="contractdocument",
            name="doc_type",
            field=models.CharField(
                choices=[
                    ("privacy_policy", "Privacy policy"),
                    ("terms_and_conditions", "Terms and conditions"),
                    ("about_app", "About app"),
                    ("reservation_notes", "Reservation notes"),
                    ("contract", "Contract"),
                ],
                default="contract",
                max_length=50,
            ),
        ),
    ]
