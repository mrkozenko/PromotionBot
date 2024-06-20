# Generated by Django 5.0.3 on 2024-06-20 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PromotionMaker', '0004_promotionpost'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpamFilterModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('black_words', models.CharField(max_length=1000, verbose_name='Заборонені слова')),
                ('except_ids', models.CharField(max_length=1000, verbose_name='ID рекламодавців виключень')),
            ],
            options={
                'verbose_name': 'Спам-фільтр',
                'verbose_name_plural': 'Спам-фільтри',
            },
        ),
    ]