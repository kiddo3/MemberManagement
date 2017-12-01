# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-27 23:04
from __future__ import unicode_literals

import alumni.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alumni', '0003_auto_20171127_1822'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentInformation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tier', alumni.fields.TierField(choices=[('st', 'Starter'), ('co', 'Contributor'), ('pa', 'Patron')], default='st', help_text='The type of your membership', max_length=2)),
                ('token', models.CharField(blank=True, max_length=255, null=True)),
                ('member', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='alumni.Alumni')),
            ],
        ),
    ]