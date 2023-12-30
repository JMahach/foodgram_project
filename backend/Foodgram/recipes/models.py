from django.core.validators import MinValueValidator
from django.db import models

from users.models import User

LETTER_LIMIT = 30


class Tag(models.Model):
    """Модель Тега."""

    name = models.CharField(
        'Название',
        unique=True,
        max_length=200
    )
    color = models.CharField(
        'Цвет',
        unique=True,
        max_length=7,
    )
    slug = models.SlugField(
        'Слаг',
        unique=True,
        max_length=200,
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

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name[:LETTER_LIMIT]


class Recipe(models.Model):
    """Модель Рецепта."""

    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэг',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиент',
        through='Amount',
        through_fields=('recipe', 'ingredient')
    )
    name = models.CharField(
        'Название',
        max_length=200
    )
    text = models.TextField(
        'Текстовое описание',
    )
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[MinValueValidator(limit_value=1)]
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:LETTER_LIMIT]


class Amount(models.Model):
    """
    Модель колличества Ингридиента.
    Cвязующщая таблица многие-ко-мнгоим для моделей Рецепта и Ингридиета.
    """

    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингридиент',
        related_name='amounts',
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        'Колличество',
        validators=[MinValueValidator(limit_value=1)]
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='amounts',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Колличество Ингридиента'
        verbose_name_plural = 'Колличества Ингридиентов'

    def __str__(self):
        return (f'{self.ingredient.name} '
                f'- {self.amount} '
                f'{self.ingredient.measurement_unit}'[:LETTER_LIMIT])


class Favorite(models.Model):
    """Модель Избранного."""

    user = models.ForeignKey(
        User,
        related_name='favorites',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return (f'{self.recipe.name} в избраннном '
                f'у {self.user.username}'[:LETTER_LIMIT])


class ShoppingList(models.Model):
    """Модель Списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Рецепт'
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_list'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return (f'{self.recipe.name} в списке покупок '
                f'у {self.user.username}'[:LETTER_LIMIT])
