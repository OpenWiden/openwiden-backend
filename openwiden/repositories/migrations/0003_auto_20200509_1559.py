# Generated by Django 3.0.5 on 2020-05-09 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repositories', '0002_auto_20200509_1417'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='repository',
            name='unique_repository',
        ),
        migrations.RenameField(
            model_name='repository',
            old_name='version_control_service',
            new_name='vcs',
        ),
        migrations.AddConstraint(
            model_name='repository',
            constraint=models.UniqueConstraint(fields=('vcs', 'remote_id'), name='unique_repository'),
        ),
    ]
