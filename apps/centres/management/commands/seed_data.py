from django.core.management.base import BaseCommand

from apps.centres.models import DiagnosticCentre, DiagnosticTest


class Command(BaseCommand):
    help = "Seeds the database with a few sample diagnostic centres and tests for manual testing."

    def handle(self, *args, **options):
        sample = {
            "City Diagnostics": {
                "location": "Pune",
                "tests": [("CBC (Complete Blood Count)", 500), ("Lipid Profile", 900), ("Thyroid Panel", 700)],
            },
            "MetroPath Labs": {
                "location": "Mumbai",
                "tests": [("X-Ray Chest", 800), ("MRI Brain", 6500), ("Blood Sugar (Fasting)", 150)],
            },
            "HealthFirst Diagnostics": {
                "location": "Bengaluru",
                "tests": [("COVID-19 RT-PCR", 600), ("Vitamin D Test", 1200), ("ECG", 400)],
            },
        }

        for centre_name, data in sample.items():
            centre, created = DiagnosticCentre.objects.get_or_create(
                name=centre_name, defaults={"location": data["location"]}
            )
            status = "created" if created else "exists"
            self.stdout.write(f"Centre '{centre_name}' {status}.")

            for test_name, price in data["tests"]:
                _, t_created = DiagnosticTest.objects.get_or_create(
                    centre=centre, name=test_name, defaults={"price": price}
                )
                if t_created:
                    self.stdout.write(f"  + Test '{test_name}' (₹{price})")

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
