from django.core.management.base import BaseCommand

from apps.tenancy.demo import seed_demo
from config.settings.base import secret


class Command(BaseCommand):
    help = "Legt zwei künstliche Hochzeiten und lokale Testkonten idempotent an."

    def handle(self, *args, **options):
        seed_demo(secret("DEMO_PASSWORD"))
        self.stdout.write(
            self.style.SUCCESS(
                "Zwei künstliche Hochzeiten und die lokalen Testrollen sind eingerichtet."
            )
        )
