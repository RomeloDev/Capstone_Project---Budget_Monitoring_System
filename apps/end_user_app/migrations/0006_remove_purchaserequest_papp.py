# Generated by Django 5.1.6 on 2025-05-01 03:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('end_user_app', '0005_purchaserequest_papp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaserequest',
            name='papp',
        ),
    ]
