from django.core.management.base import BaseCommand
from apps.communications.consumers import run_consumer


class Command(BaseCommand):
    help = 'Starts Kafka consumer for inter-service communications'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Kafka consumer..."))
        run_consumer()
        