#!/usr/bin/env python
import os

import django


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clinicSADAF.settings")
    django.setup()

    from apps.core.mock_seed import seed_mock_data

    summary = seed_mock_data()
    print("Mock data seeding completed.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
