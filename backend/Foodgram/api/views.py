from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsAdminOrAuthorOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeSerializerRead, RecipeSerializerWrite,
                             ShoppingListSerializer, SubscripeSerializer,
                             TagSerializer, UserSerializerSubscripe)
from api.utils import IngredientFilter, RecipeFilter, recipe_add_or_del
from recipes.models import (Amount, Favorite, Ingredient, Recipe, ShoppingList,
                            Tag)
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
        return recipe_add_or_del(self, request, FavoriteSerializer, Favorite)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated, )
    )
    def shopping_cart(self, request, pk):
        """Работа с списком покупок. Добавление и удаление."""
        return recipe_add_or_del(
            self,
            request,
            ShoppingListSerializer,
            ShoppingList
        )

    @action(
        detail=False,
        methods=['get', ],
        permission_classes=(IsAuthenticated, )
    )
    def download_shopping_cart(self, request):
        """Работа с списком покупок. Отправка файла со списком покупок."""
        ingredients = Amount.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            ingredient__amount=Sum('amount')
        )

        shopping_res_list = ['Список покупок:\n']
        for ingridient in ingredients:
            shopping_res_list.append(
                '\n{} - {} {}'.format(
                    ingridient['ingredient__name'],
                    ingridient['ingredient__amount'],
                    ingridient['ingredient__measurement_unit']
                )
            )

        response = HttpResponse(shopping_res_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="data.txt"'
        return response
