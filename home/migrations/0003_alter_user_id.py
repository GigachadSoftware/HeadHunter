# Generated by Django 4.2.1 on 2023-05-31 15:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0002_vacancy_is_premium"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.BigAutoField(
                default="nextval('table_name_id_seq')",
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
    ]
