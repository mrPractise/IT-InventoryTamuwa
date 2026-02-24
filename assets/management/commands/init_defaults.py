from django.core.management.base import BaseCommand
from assets.models import StatusOption, Category


class Command(BaseCommand):
    help = 'Initialize default status options and categories'

    def handle(self, *args, **options):
        # Create default status options
        statuses = [
            {'name': 'In Use', 'color': '#28a745'},
            {'name': 'Available', 'color': '#17a2b8'},
            {'name': 'Missing', 'color': '#dc3545'},
            {'name': 'Retired', 'color': '#6c757d'},
            {'name': 'Under Maintenance', 'color': '#ffc107'},
        ]
        
        for status_data in statuses:
            status, created = StatusOption.objects.get_or_create(
                name=status_data['name'],
                defaults={'color': status_data['color']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created status: {status.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Status already exists: {status.name}')
                )
        
        # Create default categories
        categories = [
            'Laptop',
            'Desktop',
            'Monitor',
            'Keyboard',
            'Mouse',
            'Printer',
            'Phone',
            'Tablet',
            'Server',
            'Network Equipment',
        ]
        
        for cat_name in categories:
            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized default data!')
        )
