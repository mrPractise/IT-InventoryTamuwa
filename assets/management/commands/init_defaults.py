"""
Initialize default data for the ICT Inventory system.
Run this after migrations: python manage.py init_defaults
"""
from django.core.management.base import BaseCommand
from assets.models import StatusOption
from maintenance.models import ActionTakenOption


class Command(BaseCommand):
    help = 'Initialize default status options and action taken options'

    def handle(self, *args, **kwargs):
        self.stdout.write('Initializing default data...')
        
        # Create default asset status options
        status_options = [
            {'name': 'In Use',              'color': '#28a745'},
            {'name': 'Available',           'color': '#17a2b8'},
            {'name': 'Missing',             'color': '#dc3545'},
            {'name': 'Retired',             'color': '#6c757d'},
            {'name': 'Under Maintenance',   'color': '#ffc107'},
        ]
        
        for option in status_options:
            status, created = StatusOption.objects.get_or_create(
                name=option['name'],
                defaults={'color': option['color'], 'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created status: {option["name"]}'))
            else:
                self.stdout.write(f'  Status already exists: {option["name"]}')
        
        # Create default maintenance action options
        action_options = [
            {'name': 'Investigation',       'description': 'Initial investigation of the issue'},
            {'name': 'Awaiting Approval',   'description': 'Waiting for approval to proceed'},
            {'name': 'De-Commissioned',     'description': 'Asset has been de-commissioned'},
            {'name': 'To Nairobi',          'description': 'Sent to Nairobi office for repairs'},
        ]
        
        for option in action_options:
            action, created = ActionTakenOption.objects.get_or_create(
                name=option['name'],
                defaults={'description': option['description'], 'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created action: {option["name"]}'))
            else:
                self.stdout.write(f'  Action already exists: {option["name"]}')
        
        self.stdout.write(self.style.SUCCESS('Default data initialization complete!'))
