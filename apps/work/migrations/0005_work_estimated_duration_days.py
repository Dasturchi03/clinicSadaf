from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("work", "0004_rename_work_x_ray_categories_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="work",
            name="estimated_duration_days",
            field=models.PositiveIntegerField(
                default=7, verbose_name="Примерная длительность (дней)"
            ),
        ),
    ]
