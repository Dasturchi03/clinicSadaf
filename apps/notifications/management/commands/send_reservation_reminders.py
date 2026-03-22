from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.utils import create_reservation_reminder_notification
from apps.reservation.models import Reservation


class Command(BaseCommand):
    help = "Send reservation reminder notifications for upcoming reservations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-ahead",
            type=int,
            default=1,
            help="How many days ahead to send reminders for.",
        )

    def handle(self, *args, **options):
        target_date = timezone.now().date() + timedelta(days=options["days_ahead"])
        reservations = Reservation.objects.filter(
            reservation_date=target_date,
            cancelled=False,
            reservation_client__client_user__isnull=False,
        ).select_related("reservation_client__client_user")

        created_count = 0
        for reservation in reservations:
            notification = create_reservation_reminder_notification(
                reservation=reservation,
                receiver=reservation.reservation_client.client_user,
            )
            if notification:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} reminder notifications for {target_date.strftime('%d-%m-%Y')}."
            )
        )
