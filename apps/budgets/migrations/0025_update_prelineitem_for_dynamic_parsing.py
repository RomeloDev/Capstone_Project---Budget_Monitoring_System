# Generated migration for dynamic PRE parsing

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0024_prebudgetrealignment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='prelineitem',
            name='excel_row_number',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text="Row number in uploaded Excel file (for debugging and traceability)"
            ),
        ),
        migrations.AddField(
            model_name='prelineitem',
            name='is_custom_item',
            field=models.BooleanField(
                default=False,
                help_text="True if this item was added by user (not in standard template)"
            ),
        ),
        migrations.AlterField(
            model_name='prelineitem',
            name='source_type',
            field=models.CharField(
                choices=[('excel', 'From Excel Template')],
                default='excel',
                help_text="All items now come from Excel (manual entry removed)",
                max_length=20
            ),
        ),
    ]
