# Generated by Django 3.0.5 on 2020-05-09 14:17

from django.db import migrations, models
import django.db.models.deletion
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_admin', models.BooleanField(default=False, verbose_name='has admin permissions')),
            ],
            options={
                'verbose_name': 'member',
                'verbose_name_plural': 'list of members',
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('version_control_service', models.CharField(choices=[('github', 'GitHub'), ('gitlab', 'Gitlab')], max_length=50, verbose_name='version control service')),
                ('remote_id', models.PositiveIntegerField(verbose_name='remote id')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='description')),
                ('url', models.URLField(blank=True, null=True, verbose_name='url')),
                ('avatar_url', models.URLField(blank=True, null=True, verbose_name='avatar url')),
                ('created_at', models.DateTimeField(blank=True, null=True, verbose_name='created at')),
                ('visibility', models.CharField(blank=True, choices=[('public', 'public'), ('private', 'private'), ('internal', 'internal')], default='public', max_length=8, verbose_name='visibility')),
            ],
            options={
                'verbose_name': 'organization',
                'verbose_name_plural': 'list of organizations',
                'ordering': ('name',),
            },
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(fields=('version_control_service', 'remote_id'), name='unique_organization'),
        ),
        migrations.AddField(
            model_name='member',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', related_query_name='member', to='organizations.Organization', verbose_name='organization'),
        ),
    ]
