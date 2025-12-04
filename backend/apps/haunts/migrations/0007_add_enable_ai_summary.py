# Generated migration for adding enable_ai_summary field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('haunts', '0006_rename_haunts_haun_created_idx_haunts_haun_created_9a3e5f_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='haunt',
            name='enable_ai_summary',
            field=models.BooleanField(
                default=True,
                help_text='Enable AI-generated summaries for changes'
            ),
        ),
    ]
