"""
Data Integrity Verification Command

This command verifies data consistency across the application and reports any issues.
Run periodically or after migrations to ensure data integrity.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from assets.models import Asset, AssignmentHistory, Person, Department
from maintenance.models import MaintenanceLog
from requisition.models import Requisition, RequisitionItem


class Command(BaseCommand):
    help = 'Verify data integrity across all models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix minor data inconsistencies automatically',
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']
        issues_found = 0
        issues_fixed = 0

        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('DATA INTEGRITY VERIFICATION'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))

        # Check 1: Assets with deleted assignments
        self.stdout.write('\n[1] Checking asset assignments...')
        orphaned_assignments = AssignmentHistory.objects.filter(
            asset__is_deleted=True
        )
        if orphaned_assignments.exists():
            count = orphaned_assignments.count()
            issues_found += count
            self.stdout.write(self.style.WARNING(f'  Found {count} assignments for deleted assets'))
            if fix_mode:
                with transaction.atomic():
                    orphaned_assignments.delete()
                issues_fixed += count
                self.stdout.write(self.style.SUCCESS(f'  Fixed: Deleted {count} orphaned assignments'))

        # Check 2: Assets assigned to deleted persons
        self.stdout.write('\n[2] Checking asset-person assignments...')
        assets_with_deleted_persons = Asset.objects.filter(
            assigned_to__isnull=False
        ).exclude(assigned_to__in=Person.objects.all())
        if assets_with_deleted_persons.exists():
            count = assets_with_deleted_persons.count()
            issues_found += count
            self.stdout.write(self.style.WARNING(f'  Found {count} assets assigned to non-existent persons'))
            if fix_mode:
                with transaction.atomic():
                    for asset in assets_with_deleted_persons:
                        asset.assigned_to = None
                        asset.save(update_fields=['assigned_to'])
                issues_fixed += count
                self.stdout.write(self.style.SUCCESS(f'  Fixed: Cleared assignments for {count} assets'))

        # Check 3: Maintenance logs for deleted assets
        self.stdout.write('\n[3] Checking maintenance logs...')
        orphaned_maintenance = MaintenanceLog.objects.filter(
            asset__is_deleted=True
        )
        if orphaned_maintenance.exists():
            count = orphaned_maintenance.count()
            issues_found += count
            self.stdout.write(self.style.WARNING(f'  Found {count} maintenance logs for deleted assets'))
            # Don't auto-delete - these are historical records

        # Check 4: Open maintenance for available assets
        self.stdout.write('\n[4] Checking maintenance status consistency...')
        from assets.models import StatusOption
        under_maintenance_status = StatusOption.objects.filter(name='Under Maintenance').first()
        available_status = StatusOption.objects.filter(name='Available').first()
        
        if under_maintenance_status and available_status:
            # Assets marked Under Maintenance but no open maintenance logs
            assets_under_maintenance = Asset.objects.filter(status=under_maintenance_status)
            for asset in assets_under_maintenance:
                open_logs = asset.maintenance_logs.filter(maintenance_status='Open')
                if not open_logs.exists():
                    issues_found += 1
                    self.stdout.write(self.style.WARNING(
                        f'  Asset {asset.asset_id} is Under Maintenance but has no open maintenance logs'
                    ))
                    if fix_mode:
                        asset.status = available_status
                        asset.save(update_fields=['status'])
                        issues_fixed += 1
                        self.stdout.write(self.style.SUCCESS(f'  Fixed: Set {asset.asset_id} to Available'))

            # Assets with open maintenance but not marked Under Maintenance
            open_maintenance = MaintenanceLog.objects.filter(maintenance_status='Open')
            for log in open_maintenance:
                if log.asset.status != under_maintenance_status:
                    issues_found += 1
                    self.stdout.write(self.style.WARNING(
                        f'  Asset {log.asset.asset_id} has open maintenance but status is {log.asset.status}'
                    ))
                    if fix_mode:
                        log.asset.status = under_maintenance_status
                        log.asset.save(update_fields=['status'])
                        issues_fixed += 1
                        self.stdout.write(self.style.SUCCESS(f'  Fixed: Set {log.asset.asset_id} to Under Maintenance'))

        # Check 5: Requisition totals consistency
        self.stdout.write('\n[5] Checking requisition totals...')
        requisitions = Requisition.objects.all()
        for req in requisitions:
            items_total = sum(item.total_price for item in req.items.all())
            if abs(items_total - req.total_amount) > 0.01:  # Allow for floating point differences
                issues_found += 1
                self.stdout.write(self.style.WARNING(
                    f'  Requisition {req.req_no}: total mismatch (stored: {req.total_amount}, calculated: {items_total})'
                ))
                if fix_mode:
                    req.total_amount = items_total
                    req.save(update_fields=['total_amount'])
                    issues_fixed += 1
                    self.stdout.write(self.style.SUCCESS(f'  Fixed: Updated total for {req.req_no}'))

        # Check 6: Department consistency
        self.stdout.write('\n[6] Checking department consistency...')
        persons_without_dept = Person.objects.filter(department__isnull=True)
        if persons_without_dept.exists():
            count = persons_without_dept.count()
            self.stdout.write(self.style.WARNING(f'  Found {count} persons without a department'))
            # This might be valid, so just report it

        # Summary
        self.stdout.write('\n' + '=' * 60)
        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS('✓ All data integrity checks passed!'))
        else:
            self.stdout.write(self.style.WARNING(f'Total issues found: {issues_found}'))
            if fix_mode:
                self.stdout.write(self.style.SUCCESS(f'Total issues fixed: {issues_fixed}'))
                remaining = issues_found - issues_fixed
                if remaining > 0:
                    self.stdout.write(self.style.ERROR(f'Remaining issues: {remaining}'))
        self.stdout.write('=' * 60)
