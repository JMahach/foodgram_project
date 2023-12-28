from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

LETTER_LIMIT = 30

User = get_user_model()


class Tag(models.Model):
    """Модель Тега."""

    name = models.CharField('Название', max_length=200)
    color = models.CharField(
        'Цвет',
        max_length=7,
        blank=True,
        null=True
    )
    slug = models.SlugField(
        'Слаг',
        unique=True,
        max_length=200,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name[:LETTER_LIMIT]

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    """Модель Ингридиента."""

    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Eдиница измерения', max_length=10)

    def __str__(self):
        return self.name[:LETTER_LIMIT]

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Recipe(models.Model):
    """Модель Рецепта."""

    # is_favorited =
    # is_in_shopping_cart =
    # image =
    # author = models.ForeignKey(
    #     User,
    #     related_name='recipes',
    #     on_delete=models.CASCADE,
    #     verbose_name='Автор рецепта'
    # )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэг',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиент',
        through='Amount'
    )
    name = models.CharField(
        'Название',
        max_length=200
    )
    text = models.TextField(
        'Текстовое описание',
        help_text='Введите текст поста'
    )
    cooking_time = models.IntegerField(
        'Время готовки',
        validators=[MinValueValidator(limit_value=1)]
    )

    def __str__(self):
        return self.name[:LETTER_LIMIT]

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Amount(models.Model):
    """Модель колличества Ингридиента."""

    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингридиент',
        related_name='amounts',
        on_delete=models.PROTECT
    )
    amount = models.IntegerField(
        'Колличество',
        validators=[MinValueValidator(limit_value=1)]
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='amounts',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return (f'{self.ingredient.name}'
                f'- {self.amount} {self.ingredient.measurement_unit}')

    class Meta:
        verbose_name = 'Колличество Ингридиента'
        verbose_name_plural = 'Колличества Ингридиента'
