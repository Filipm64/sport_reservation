from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('reservations', '0003_remove_draft_lifecycle')]

    operations = [
        migrations.AddField(
            model_name='resource', name='cancellation_notice_minutes',
            field=models.PositiveIntegerField(
                default=120, verbose_name='Storno lhůta (minuty)',
                help_text='Platí pouze pro nově vytvořené rezervace. 0 = kdykoliv před začátkem.',
            ),
        ),
        migrations.AddField(
            model_name='reservation', name='cancellation_notice_minutes',
            field=models.PositiveIntegerField(
                default=0, verbose_name='Uložená storno lhůta (minuty)',
            ),
            preserve_default=False,
        ),
    ]
