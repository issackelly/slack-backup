# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backupdata', '0002_auto_20150102_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='is_im',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
