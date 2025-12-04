# Generated migration for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('haunts', '0004_alter_haunt_config_alter_haunt_current_state'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='haunt',
            index=models.Index(fields=['-created_at'], name='haunts_haun_created_idx'),
        ),
    ]
