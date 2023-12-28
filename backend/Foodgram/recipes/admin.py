from django.contrib import admin
from recipes.models import Ingredient, Recipe, Tag

admin.site.empty_value_display = '-пусто-'


@admin.register(Tag)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        # 'author',
        'name',
        'text',
        'cooking_time'
    )
    search_fields = ('name',)

    def display_tags(self, obj):
        return ', '.join(tag for tag in obj.tags.all())
    display_tags.short_description = 'tags'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
