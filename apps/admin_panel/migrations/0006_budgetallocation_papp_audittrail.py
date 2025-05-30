# Generated by Django 5.1.6 on 2025-05-01 01:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0005_budgetallocation_remaining_budget'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetallocation',
            name='papp',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.CreateModel(
            name='AuditTrail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(max_length=100)),
                ('action', models.CharField(choices=[('LOGIN', 'Login'), ('LOGOUT', 'Logout'), ('APPROVED', 'Approved Request'), ('DENIED', 'Denied Request'), ('REALIGN', 'Realignment Submitted'), ('ALLOCATE', 'Budget Allocated'), ('ADD_FUNDS', 'Institutional Fund Added')], max_length=20)),
                ('description', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
