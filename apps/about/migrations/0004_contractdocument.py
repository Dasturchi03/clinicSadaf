from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("about", "0003_alter_article_article_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContractDocument",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True, editable=False)),
                ("contract_id", models.AutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("file", models.FileField(upload_to="contracts/")),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
    ]
