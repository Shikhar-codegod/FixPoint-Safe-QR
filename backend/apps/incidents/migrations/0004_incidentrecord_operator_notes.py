from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('incidents', '0003_migrate_incident_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidentrecord',
            name='operator_notes',
            field=models.TextField(blank=True),
        ),
    ]
