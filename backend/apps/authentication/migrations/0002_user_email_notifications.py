# Generated migration for email notification preferences

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_notifications_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Enable email notifications for haunt changes'
            ),
        ),
    ]
