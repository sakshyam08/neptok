# Generated manually to add views and earnings fields to Application model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='views',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='application',
            name='earnings',
            field=models.DecimalField(decimal_places=2, default=0.00, max_digits=10),
        ),
    ] 