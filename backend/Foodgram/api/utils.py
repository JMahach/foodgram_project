import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import FilterSet, filters
from rest_framework import serializers, status
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, Tag


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для работы с картинками в сериализаторх."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientFilter(FilterSet):
    """
    Поиск по полю name без учета регистра начиная с начала строки.
    Используется в Ingredient преставлении.
    """
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )


class RecipeFilter(FilterSet):
    """
    Поиск по полям tags и author.
    Добавлят возможность фильровать по избранным
    и добавленным в корзину рецептам.
    Используется в Recipe преставлении.
    """

    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             to_field_name='slug',
                                             queryset=Tag.objects.all())
    is_favorited = filters.BooleanFilter(
        method='is_favorited_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter')

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_list__user=user)
        return queryset


def model_add_delete(self, request, Serializer, Model):
    """
    Вспомогательная функция для добавления и удаления рецепта
    в избранное или список покупок.
    """

    recipe = self.get_object()
    if request.method == 'POST':
        serializer = Serializer(
            data={
                'user': request.user.pk,
                'recipe': recipe.pk
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    get_object_or_404(
        Model,
        user=request.user,
        recipe=recipe).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
