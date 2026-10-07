from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0097_alter_application_notes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='jobapplication',
            name='rejected_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who rejected this application',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='jobapplication_rejections',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
