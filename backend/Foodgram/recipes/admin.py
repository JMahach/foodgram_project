from django.contrib import admin
from recipes.models import (Amount, Favorite, Ingredient, Recipe, ShoppingList,
                            Tag)

admin.site.empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = Amount


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'favorites_count',
    )
    search_fields = ('name', 'tags', 'author')
    inlines = [
        RecipeIngredientInline,
    ]

    def favorites_count(self, obj):
        """Возврашает количество добавлений Рецепта в избранное."""
        return obj.favorites.count()

    favorites_count.short_description = 'Число добавлений рецепта в избранное'


@admin.register(Amount)
class AmountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
