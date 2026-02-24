from django.core.management.base import BaseCommand
from maintenance.models import ActionTakenOption


class Command(BaseCommand):
    help = 'Initialize default maintenance action options'

    def handle(self, *args, **options):
        actions = [
            'Awaiting approval for repair',
            'De-Commissioned',
            'Investigation',
            'To Nairobi',
        ]
        
        for action_name in actions:
            action, created = ActionTakenOption.objects.get_or_create(name=action_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created action: {action.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Action already exists: {action.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized maintenance actions!')
        )
