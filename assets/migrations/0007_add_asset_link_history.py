# Generated manually for AssetLinkHistory model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0006_assetlink_assetlink_unique_asset_link'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetLinkHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('linked_at', models.DateTimeField(blank=True, null=True)),
                ('unlinked_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='link_history_from', to='assets.asset')),
                ('linked_asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='link_history_to', to='assets.asset')),
                ('unlinked_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-unlinked_at'],
            },
        ),
        migrations.AddIndex(
            model_name='assetlinkhistory',
            index=models.Index(fields=['asset', 'unlinked_at'], name='assets_asso_asset_i_1f76c3_idx'),
        ),
        migrations.AddIndex(
            model_name='assetlinkhistory',
            index=models.Index(fields=['linked_asset', 'unlinked_at'], name='assets_asso_linked__2c4f9e_idx'),
        ),
    ]
