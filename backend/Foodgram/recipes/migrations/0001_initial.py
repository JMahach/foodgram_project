# Generated by Django 3.2 on 2023-12-27 19:56

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Amount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1)], verbose_name='Колличество')),
            ],
            options={
                'verbose_name': 'Колличество Ингридиента',
                'verbose_name_plural': 'Колличества Ингридиента',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('measurement_unit', models.CharField(max_length=10, verbose_name='Eдиница измерения')),
            ],
            options={
                'verbose_name': 'Ингридиент',
                'verbose_name_plural': 'Ингридиенты',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('color', models.CharField(blank=True, max_length=7, null=True, verbose_name='Цвет')),
                ('slug', models.SlugField(blank=True, max_length=200, null=True, unique=True, verbose_name='Слаг')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('text', models.TextField(help_text='Введите текст поста', verbose_name='Текстовое описание')),
                ('cooking_time', models.IntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1)], verbose_name='Время готовки')),
                ('ingredients', models.ManyToManyField(through='recipes.Amount', to='recipes.Ingredient')),
                ('tags', models.ManyToManyField(blank=True, null=True, to='recipes.Tag', verbose_name='Тэг')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
            },
        ),
        migrations.AddField(
            model_name='amount',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='amounts', to='recipes.ingredient', verbose_name='Ингридиент'),
        ),
        migrations.AddField(
            model_name='amount',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amounts', to='recipes.recipe', verbose_name='Рецепт'),
        ),
    ]