# Generated by Django 2.1.7 on 2019-03-30 12:31

from django.db import migrations, models
import django.db.models.deletion

import stripe
from datetime import datetime

def createLegacySetup(apps, schema_editor):
    PaymentInformation = apps.get_model('payments', 'PaymentInformation')
    SetupCompleted = apps.get_model('alumni', 'SetupCompleted')

    for pi in PaymentInformation.objects.all():
        setup, created = SetupCompleted.objects.get_or_create(member=pi.member)
        setup.date = pi.member.profile.date_joined
        setup.save()

class Migration(migrations.Migration):

    dependencies = [
        ('alumni', '0015_auto_20190318_2009'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SetupCompleted',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('member', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='setup', to='alumni.Alumni')),
            ],
        ),
        migrations.RunPython(createLegacySetup)
    ]
