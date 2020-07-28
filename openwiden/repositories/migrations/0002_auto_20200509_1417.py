# Generated by Django 3.0.5 on 2020-05-09 14:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('repositories', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='repositories', related_query_name='repository', to='users.VCSAccount', verbose_name='owner'),
        ),
        migrations.AddField(
            model_name='issue',
            name='repository',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issues', related_query_name='issue', to='repositories.Repository', verbose_name='repository'),
        ),
        migrations.AddConstraint(
            model_name='repository',
            constraint=models.UniqueConstraint(fields=('version_control_service', 'remote_id'), name='unique_repository'),
        ),
        migrations.AddConstraint(
            model_name='issue',
            constraint=models.UniqueConstraint(fields=('repository', 'remote_id'), name='unique_issue'),
        ),
    ]
