from api.serializers import (IngredientSerializer,
                             RecipeSerializerRead,
                             RecipeSerializer,
                             TagSerializer)
from recipes.models import Ingredient, Recipe, Tag
from rest_framework import mixins, viewsets


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet модели Recipe."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    # def perform_create(self, serializer):
    #     """Сохранение автора отзыва"""
    #     serializer.save(author=self.request.user)

    # def get_serializer_class(self):
    #     if self.action == 'list' or self.action == 'retrieve':
    #         return RecipeSerializerRead
    #     elif self.action == 'create' or self.action == 'update':
    #         return RecipeSerializerWrite

    def perform_create(self, serializer):
        # Дополнительная логика при создании объекта
        serializer.save()

    def perform_update(self, serializer):
        # Дополнительная логика при обновлении объекта
        serializer.save()
