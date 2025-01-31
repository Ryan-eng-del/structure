# Generated by Django 4.2 on 2024-03-25 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0005_algorithmsystemruntimecontrol_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='algorithmprocessqueue',
            name='state',
            field=models.CharField(choices=[('pending', 'pending'), ('running', 'running')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='algorithmtask',
            name='status',
            field=models.CharField(choices=[('running', 'running'), ('success', 'success'), ('canceled', 'canceled'), ('created', 'created'), ('pending', 'pending')], default='pending', max_length=32),
        ),
    ]
