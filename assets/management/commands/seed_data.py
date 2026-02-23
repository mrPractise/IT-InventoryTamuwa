import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from assets.models import Asset, Category, StatusOption, Department, AssignmentHistory


class Command(BaseCommand):
    help = 'Seed the database with 10 dummy assets for testing'

    ASSETS = [
        {
            'asset_id': 'LPT-001',
            'category': 'Laptop',
            'model_description': 'Dell Latitude 5520 Core i7',
            'serial_number': 'SN-DL5520-001',
            'purchase_date': '2022-03-15',
            'department': 'IT',
            'status': 'In Use',
            'assign': True,
        },
        {
            'asset_id': 'LPT-002',
            'category': 'Laptop',
            'model_description': 'HP EliteBook 840 G8',
            'serial_number': 'SN-HP840-002',
            'purchase_date': '2022-06-10',
            'department': 'Finance',
            'status': 'In Use',
            'assign': True,
        },
        {
            'asset_id': 'DSK-001',
            'category': 'Desktop',
            'model_description': 'HP ProDesk 400 G7 Core i5',
            'serial_number': 'SN-HPD400-001',
            'purchase_date': '2021-11-20',
            'department': 'HR',
            'status': 'In Use',
            'assign': True,
        },
        {
            'asset_id': 'MON-001',
            'category': 'Monitor',
            'model_description': 'Dell UltraSharp 27" U2722D',
            'serial_number': 'SN-DLU27-001',
            'purchase_date': '2022-03-15',
            'department': 'IT',
            'status': 'In Use',
            'assign': False,
        },
        {
            'asset_id': 'LPT-003',
            'category': 'Laptop',
            'model_description': 'Lenovo ThinkPad X1 Carbon Gen 9',
            'serial_number': 'SN-LNVX1-003',
            'purchase_date': '2021-09-05',
            'department': 'Management',
            'status': 'Available',
            'assign': False,
        },
        {
            'asset_id': 'PRT-001',
            'category': 'Printer',
            'model_description': 'Canon imageRUNNER 2625',
            'serial_number': 'SN-CN2625-001',
            'purchase_date': '2020-05-30',
            'department': 'Admin',
            'status': 'Under Maintenance',
            'assign': False,
        },
        {
            'asset_id': 'NET-001',
            'category': 'Network Equipment',
            'model_description': 'Cisco Catalyst 2960-X 48-Port Switch',
            'serial_number': 'SN-CSC2960-001',
            'purchase_date': '2019-08-12',
            'department': 'IT',
            'status': 'In Use',
            'assign': False,
        },
        {
            'asset_id': 'TAB-001',
            'category': 'Tablet',
            'model_description': 'Samsung Galaxy Tab S8',
            'serial_number': 'SN-SGTS8-001',
            'purchase_date': '2023-01-20',
            'department': 'Sales',
            'status': 'In Use',
            'assign': True,
        },
        {
            'asset_id': 'PHN-001',
            'category': 'Phone',
            'model_description': 'Samsung Galaxy A53 5G',
            'serial_number': 'SN-SGA53-001',
            'purchase_date': '2022-07-14',
            'department': 'Sales',
            'status': 'Available',
            'assign': False,
        },
        {
            'asset_id': 'LPT-004',
            'category': 'Laptop',
            'model_description': 'Acer Aspire 5 Core i5',
            'serial_number': 'SN-ACER5-004',
            'purchase_date': '2020-03-22',
            'department': 'Finance',
            'status': 'Retired',
            'assign': False,
        },
    ]

    DEPARTMENTS = ['IT', 'Finance', 'HR', 'Management', 'Admin', 'Sales']

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing seed assets and re-seed from scratch',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('--- Seeding dummy data ---'))

        if options['reset']:
            seed_ids = [a['asset_id'] for a in self.ASSETS]
            deleted, _ = Asset.objects.filter(asset_id__in=seed_ids).delete()
            self.stdout.write(self.style.WARNING(f'  Deleted {deleted} existing seed asset(s)'))

        # 1. Ensure default statuses exist
        status_defaults = [
            {'name': 'In Use',            'color': '#28a745'},
            {'name': 'Available',         'color': '#17a2b8'},
            {'name': 'Under Maintenance', 'color': '#ffc107'},
            {'name': 'Missing',           'color': '#dc3545'},
            {'name': 'Retired',           'color': '#6c757d'},
        ]
        for sd in status_defaults:
            StatusOption.objects.get_or_create(name=sd['name'], defaults={'color': sd['color']})
        self.stdout.write(self.style.SUCCESS('✔ Status options ready'))

        # 2. Ensure departments exist
        for dept_name in self.DEPARTMENTS:
            Department.objects.get_or_create(name=dept_name)
        self.stdout.write(self.style.SUCCESS('✔ Departments ready'))

        # 3. Ensure categories exist
        for asset_data in self.ASSETS:
            Category.objects.get_or_create(name=asset_data['category'])
        self.stdout.write(self.style.SUCCESS('✔ Categories ready'))

        # 4. Get or create a test user for assignments
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'testuser@tamuwa.local',
                'is_staff': False,
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            self.stdout.write(self.style.SUCCESS(
                '✔ Test user created (username: testuser / password: testpass123)'
            ))
        else:
            self.stdout.write(self.style.WARNING('  Test user already exists, skipping'))

        admin_user = User.objects.filter(is_superuser=True).first() or test_user

        # 5. Seed assets
        # We use Model.save() directly (bypassing full_clean) so that:
        # - post_save signals fire  → AssignmentHistory records are created
        # - But we avoid the full_clean validation that could reject seed data
        from django.db.models import Model as DjangoModel

        created_count = 0
        skipped_count = 0

        for data in self.ASSETS:
            if Asset.objects.filter(asset_id=data['asset_id']).exists():
                self.stdout.write(self.style.WARNING(
                    f"  Skipped (already exists): {data['asset_id']}"
                ))
                skipped_count += 1
                continue

            category   = Category.objects.get(name=data['category'])
            status     = StatusOption.objects.get(name=data['status'])
            department = Department.objects.get(name=data['department'])
            assigned   = test_user if data['assign'] else None

            asset = Asset(
                asset_id=data['asset_id'],
                category=category,
                model_description=data['model_description'],
                serial_number=data['serial_number'],
                purchase_date=data['purchase_date'],
                department=department,
                status=status,
                assigned_to=assigned,
                created_by=admin_user,
                updated_by=admin_user,
            )
            # Save via base Model.save() to skip full_clean but still fire signals
            DjangoModel.save(asset)

            # Explicitly create AssignmentHistory for assigned assets
            # (the post_save signal does this too, but being explicit here
            #  ensures it's always created regardless of signal state)
            if assigned:
                AssignmentHistory.objects.get_or_create(
                    asset=asset,
                    user=assigned,
                    end_date__isnull=True,
                    defaults={'start_date': timezone.now()},
                )

            created_count += 1
            assign_note = f' → assigned to {assigned.username}' if assigned else ''
            self.stdout.write(self.style.SUCCESS(
                f'  ✔ Created: {data["asset_id"]} — {data["model_description"]}{assign_note}'
            ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! {created_count} asset(s) created, {skipped_count} skipped.'
        ))
