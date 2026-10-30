import time
import logging
from django.core.management.base import BaseCommand
from apps.notifications.services import process_due_chains

logger = logging.getLogger('apps.notifications')

class Command(BaseCommand):
    help = "Runs continuous background notification sweeper loop to process due chains without Redis."

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=2,
            help="Polling interval in seconds between sweeper passes (default: 2)."
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help="Run a single sweeper pass and exit."
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']

        self.stdout.write(self.style.SUCCESS(
            f"Starting FixPoint notification sweeper (interval={interval}s, once={run_once})..."
        ))

        try:
            while True:
                count = process_due_chains()
                if count > 0:
                    self.stdout.write(self.style.NOTICE(f"Processed {count} due notification chain(s)."))
                if run_once:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Notification sweeper terminated by user."))
