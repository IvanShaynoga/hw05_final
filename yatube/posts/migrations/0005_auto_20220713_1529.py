# Generated by Django 2.2.16 on 2022-07-13 12:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auto_20220624_1147'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-pub_date',), 'verbose_name': 'запись', 'verbose_name_plural': 'Записи'},
        ),
    ]
