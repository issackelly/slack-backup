# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0003_auto_20150103_0633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='slack_access_token',
            field=models.CharField(default=b'', max_length=120),
            preserve_default=True,
        ),
    ]
