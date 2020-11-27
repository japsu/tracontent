# Generated by Django 3.1.3 on 2020-11-27 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracommon', '0002_artist_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artist',
            name='day',
            field=models.CharField(choices=[('vkl', 'Koko viikonloppu'), ('la', 'Vain lauantai'), ('su', 'Vain sunnuntai')], default='vkl', max_length=3),
        ),
    ]
