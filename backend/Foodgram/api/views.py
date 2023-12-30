from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, views, viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsAdminOrAuthorOrReadOnly
from api.serializers import (IngredientSerializer, FavoriteSerializer,
                             RecipeSerializerRead, RecipeSerializerWrite,
                             ShoppingListSerializer, SubscripeSerializer,
                             TagSerializer, UserSerializerSubscripe)
from api.utils import IngredientFilter, RecipeFilter
from recipes.models import Ingredient, Favorite, Recipe, ShoppingList, Tag
from users.models import Subscription, User


class UserSubscribtionsListView(generics.ListAPIView):
    """View для получения списка подписок."""

    serializer_class = UserSerializerSubscripe

    def get_queryset(self):
        subscriptions = Subscription.objects.filter(user=self.request.user)
        subscribed_users = subscriptions.values_list('author', flat=True)
        authors = User.objects.filter(pk__in=subscribed_users)
        return authors


class UserSubscribeView(views.APIView):
    """View для создания и удаления подписок."""

    def post(self, request, user_id):
        """Создает подписку."""
        author = get_object_or_404(User, id=user_id)
        serializer = SubscripeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        """Удаляет подписку."""
        author = get_object_or_404(User, id=user_id)
        if Subscription.objects.filter(user=request.user,
                                       author=author).exists():
            Subscription.objects.get(user=request.user.id,
                                     author=user_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Вы еще не подписаны на этого Автора'},
            status=status.HTTP_400_BAD_REQUEST
        )


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny, )


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny, )

    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAdminOrAuthorOrReadOnly, )
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        """Сохранение автора отзыва при создании Рецепта."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Выбор сериалайзера для чтения или записи."""
        if self.action in ('list', 'retrieve'):
            return RecipeSerializerRead
        return RecipeSerializerWrite

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated, )
    )
    def favorite(self, request, pk):
        """Работа с избранными рецептами. Добавление и удаление."""
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={
                    'user': request.user.pk,
                    'recipe': recipe.pk
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(
                Favorite,
                user=request.user,
                recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated, )
    )
    def shopping_cart(self, request, pk):
        """Работа с списком покупок рецептами. Добавление и удаление."""
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = ShoppingListSerializer(
                data={
                    'user': request.user.pk,
                    'recipe': recipe.pk
                },
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(
                ShoppingList,
                user=request.user,
                recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get',],
        permission_classes=(IsAuthenticated, )
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        # ingredients = Amount.objects.filter(
        #     recipe__carts__user=request.user
        # ).values(
        #     'ingredient__name', 'ingredient__measurement_unit'
        # ).annotate(ingredient_amount=Sum('amount'))
        # shopping_list = ['Список покупок:\n']
        # for ingredient in ingredients:
        #     name = ingredient['ingredient__name']
        #     unit = ingredient['ingredient__measurement_unit']
        #     amount = ingredient['ingredient_amount']
        #     shopping_list.append(f'\n{name} - {amount}, {unit}')
        # response = HttpResponse(shopping_list, content_type='text/plain')
        # response['Content-Disposition'] = \
        #     'attachment; filename="shopping_cart.txt"'
        # return response
        # pass
