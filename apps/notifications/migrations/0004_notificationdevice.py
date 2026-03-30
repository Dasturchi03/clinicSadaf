from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_alter_user_user_gender"),
        ("notifications", "0003_notification_is_read_notification_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationDevice",
            fields=[
                ("device_id", models.AutoField(primary_key=True, serialize=False)),
                ("token", models.CharField(max_length=512, unique=True)),
                (
                    "platform",
                    models.CharField(
                        choices=[
                            ("android", "Android"),
                            ("ios", "iOS"),
                            ("web", "Web"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=32,
                    ),
                ),
                ("device_uid", models.CharField(blank=True, max_length=255, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_devices",
                        to="user.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Устройство уведомлений",
                "verbose_name_plural": "Устройства уведомлений",
                "default_permissions": (),
                "permissions": [
                    ("add_notificationdevice", "Добавить устройство уведомлений"),
                    ("view_notificationdevice", "Просмотреть устройство уведомлений"),
                    ("change_notificationdevice", "Изменить устройство уведомлений"),
                    ("delete_notificationdevice", "Удалить устройство уведомлений"),
                ],
            },
        ),
    ]
