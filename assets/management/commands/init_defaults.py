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
        
        # Create default status options
        status_options = [
            {'name': 'In Use', 'color': '#28a745'},
            {'name': 'Available', 'color': '#17a2b8'},
            {'name': 'Under Maintenance', 'color': '#ffc107'},
            {'name': 'Missing', 'color': '#dc3545'},
            {'name': 'Retired', 'color': '#6c757d'},
        ]
        
        for option in status_options:
            status, created = StatusOption.objects.get_or_create(
                name=option['name'],
                defaults={'color': option['color'], 'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created status: {option["name"]}'))
            else:
                self.stdout.write(f'Status already exists: {option["name"]}')
        
        # Create default action taken options
        action_options = [
            {'name': 'Investigation', 'description': 'Initial investigation of the issue'},
            {'name': 'Waiting Approval', 'description': 'Waiting for approval to proceed'},
            {'name': 'To Nairobi', 'description': 'Sent to Nairobi for repairs'},
            {'name': 'Decommissioned', 'description': 'Asset has been decommissioned'},
        ]
        
        for option in action_options:
            action, created = ActionTakenOption.objects.get_or_create(
                name=option['name'],
                defaults={'description': option['description'], 'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created action: {option["name"]}'))
            else:
                self.stdout.write(f'Action already exists: {option["name"]}')
        
        self.stdout.write(self.style.SUCCESS('Default data initialization complete!'))
