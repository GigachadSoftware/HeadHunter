# Generated by Django 4.2.1 on 2023-05-31 15:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0003_alter_user_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.BigAutoField(
                db_index=True, primary_key=True, serialize=False, unique=True
            ),
        ),
    ]
