# Generated migration for PRE approved documents

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('budgets', '0025_update_prelineitem_for_dynamic_parsing'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentPREApprovedDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(
                    upload_to='pre_approved_uploads/%Y/%m/',
                    validators=[django.core.validators.FileExtensionValidator(
                        allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
                    )],
                    help_text="Signed/approved document uploaded by end user"
                )),
                ('file_name', models.CharField(max_length=255)),
                ('file_size', models.IntegerField(help_text="File size in bytes")),
                ('document_type', models.CharField(
                    max_length=50,
                    choices=[
                        ('signed_pre', 'Signed PRE Document'),
                        ('signed_supporting', 'Signed Supporting Document'),
                    ],
                    default='signed_pre'
                )),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, help_text="Optional description")),
                ('uploaded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    related_name='uploaded_pre_approved_documents'
                )),
                ('pre', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='approved_documents',
                    to='budgets.departmentpre'
                )),
            ],
            options={
                'verbose_name': 'PRE Approved Document',
                'verbose_name_plural': 'PRE Approved Documents',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.AddField(
            model_name='departmentpre',
            name='awaiting_verification',
            field=models.BooleanField(
                default=False,
                help_text="True when end user has uploaded signed documents, awaiting admin verification"
            ),
        ),
        migrations.AddField(
            model_name='departmentpre',
            name='end_user_uploaded_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Timestamp when end user uploaded signed documents"
            ),
        ),
        migrations.AlterField(
            model_name='departmentpre',
            name='status',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('Draft', 'Draft'),
                    ('Pending', 'Pending Review'),
                    ('Partially Approved', 'Partially Approved'),
                    ('Awaiting Admin Verification', 'Awaiting Admin Verification'),
                    ('Approved', 'Approved'),
                    ('Rejected', 'Rejected'),
                ],
                default='Draft'
            ),
        ),
    ]
