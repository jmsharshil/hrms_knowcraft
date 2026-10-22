# Generated 2026-10-20
#
# Converts hod (FK → User) to hod_email (EmailField)
# Converts reporting_manager (FK → User) to reporting_manager_email (EmailField)
#
# HOW TO APPLY:
#   Live server  : python manage.py migrate          (runs 0102 normally)
#   Local server : python manage.py migrate jobs 0102 --fake
#                  (local DB already has EmailField columns from the rewritten 0101)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0101_jobapplication_reporting_manager_team_shift'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── hod FK  →  hod_email EmailField ──────────────────────────────────
        migrations.RemoveField(
            model_name='jobapplication',
            name='hod',
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='hod_email',
            field=models.EmailField(
                blank=True,
                null=True,
                help_text=(
                    'HOD email for this hire. '
                    'If set, onboarding emails go here instead of the MRF requester.'
                ),
                max_length=254,
            ),
        ),

        # ── reporting_manager FK  →  reporting_manager_email EmailField ───────
        migrations.RemoveField(
            model_name='jobapplication',
            name='reporting_manager',
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='reporting_manager_email',
            field=models.EmailField(
                blank=True,
                null=True,
                help_text='Reporting Manager email for this hire.',
                max_length=254,
            ),
        ),
    ]
