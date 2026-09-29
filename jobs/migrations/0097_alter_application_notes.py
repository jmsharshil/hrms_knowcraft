# Rewritten to safely handle existing plain-text data in the notes column.
# Strategy: use ALTER TABLE ... USING to convert text → jsonb in one step.
#   - Blank / empty string  →  '[]'::jsonb
#   - Non-empty plain text  →  a JSON array with one entry {text, author_name, timestamp}
# This avoids the "invalid input syntax for type json" DataError from the
# auto-generated AlterField which tries to cast text directly to jsonb.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0096_application_is_tagged'),
    ]

    operations = [
        # Step 1: convert the column in-place using a USING expression.
        # Existing plain text is wrapped in a JSON array so no data is lost.
        migrations.RunSQL(
            sql="""
                ALTER TABLE applications
                ALTER COLUMN notes TYPE jsonb
                USING CASE
                    WHEN notes IS NULL OR TRIM(notes) = ''
                        THEN '[]'::jsonb
                    ELSE json_build_array(
                        json_build_object(
                            'text',        notes,
                            'author_name', 'Migrated',
                            'author_id',   '',
                            'timestamp',   to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
                        )
                    )::jsonb
                END;
            """,
            reverse_sql="""
                ALTER TABLE applications
                ALTER COLUMN notes TYPE text
                USING COALESCE(
                    (SELECT elem->>'text'
                     FROM jsonb_array_elements(notes) AS elem
                     LIMIT 1),
                    ''
                );
            """,
        ),

        # Step 2: tell Django the field is now a JSONField (updates django_migrations /
        # schema state so future makemigrations compares correctly).
        migrations.AlterField(
            model_name='application',
            name='notes',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Structured note entries: [{text, author_name, author_id, timestamp}]',
            ),
        ),
    ]
