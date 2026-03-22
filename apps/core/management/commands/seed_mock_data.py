from django.core.management.base import BaseCommand

from apps.core.mock_seed import seed_mock_data


class Command(BaseCommand):
    help = "Fill database with linked mock data for Clinicsadaf testing."

    def handle(self, *args, **options):
        summary = seed_mock_data(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS("Mock data seeding completed."))
        for key, value in summary.items():
            self.stdout.write(f"{key}: {value}")
