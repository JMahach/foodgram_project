from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.utils import Base64ImageField, add_ingredients
from recipes.models import (Amount, Favorite, Ingredient, Recipe, ShoppingList,
                            Tag)
from users.models import Subscription, User


class UserSerializerWrite(UserCreateSerializer):
    """Serializer для модели User для создания пользователей."""

    class Meta:
        model = User
        fields = ('email',
                  'username',
                  'first_name',
                  'last_name',
                  'password')


class UserSerializerRead(UserSerializer):
    """Serializer для модели User для чтения."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        """
        Добавляет в ответ булево поле подписан ли
        текущий юзер на запрощеного пользователя.
        """
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Subscription.objects.filter(
                    user=request.user,
                    author=obj
                ).exists())


class UserSerializerSubscripe(UserSerializerRead):
    """
    Serializer для модели User для возвращения информации о подписках.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Добавляет в ответ поле с кратким описанием рецептов Пользователя."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit:
            if int(recipes_limit) < 1:
                raise serializers.ValidationError(
                    {'QUERY PARAMETERS': 'recipes_limit должен быть больше 0.'}
                )
            recipes = recipes[:int(recipes_limit)]

        return RecipeSerializerBrief(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        """Добавляет в ответ поле с количеством рецептов Пользователя."""
        return obj.recipes.count()


class SubscripeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора.'
            )
        ]

    def validate(self, data):
        """Валидация полей."""
        request = self.context.get('request')
        if request.user == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя.'
            )
        return data

    def to_representation(self, instance):
        """Логика ответа после создания Подписки."""
        request = self.context.get('request')
        return UserSerializerSubscripe(
            instance.author,
            context={'request': request}
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Serializer для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientSerializerWrite(serializers.Serializer):
    """Serializer для связанного поля ingredients в RecipeSerializerWrite."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()


class IngredientSerializerRead(serializers.ModelSerializer):
    """Serializer для связанного поля ingredients в RecipeSerializerRead."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = Amount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializerWrite(serializers.ModelSerializer):
    """Serializer модели Recipe для записи."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientSerializerWrite(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        """Валидация полей."""
        errors = {}
        ingredients_errors = {}
        ingredients = set()

        for ingredient in data.get('ingredients', []):
            if ingredient['id'] in ingredients:
                ingredients_errors['id'] = (
                    'Вы пытаетесь добавить в рецепт два одинаковых ингредиента'
                )
            ingredients.add(ingredient['id'])
            if int(ingredient['amount']) < 1:
                ingredients_errors['amount'] = (
                    'Количество должно быть больше 0'
                )

        if not data.get('tags'):
            errors['tags'] = 'Необходимо указать минимум 1 тег.'
        if not data.get('ingredients'):
            errors['ingredients'] = 'Необходимо указать минимум 1 ингредиент.'
        if ingredients_errors:
            errors['ingredients'] = ingredients_errors
        if errors:
            raise serializers.ValidationError(errors)

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Сохранение Рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags_data)
        add_ingredients(ingredients_data, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Изменение Рецепта."""

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        super().update(instance, validated_data)

        instance.tags.set(tags_data)
        instance.amounts.all().delete()
        add_ingredients(ingredients_data, instance)

        return instance

    def to_representation(self, instance):
        """Логика ответа после создания или обновления Рецепта."""
        request = self.context.get('request')
        return RecipeSerializerRead(
            instance,
            context={'request': request}
        ).data


class RecipeSerializerRead(serializers.ModelSerializer):
    """Serializer модели Recipe для чтения."""

    author = UserSerializerRead(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientSerializerRead(many=True, read_only=True,
                                           source='amounts')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        """
        Добавляет в ответ булево поле добавлен ли
        рецепт в избранное текущего пользователя.
        """
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.favorites.filter(user=request.user.id).exists())

    def get_is_in_shopping_cart(self, obj):
        """
        Добавляет в ответ булево поле добавлен ли
        рецепт в список покпок текущего пользователя.
        """
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.shopping_list.filter(user=request.user.id).exists())


class RecipeSerializerBrief(serializers.ModelSerializer):
    """Serializer модели Recipe для работы с краткой информацией о рецепте."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer модели Favorite."""

    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном.'
            )
        ]

    def to_representation(self, instance):
        """Логика ответа после добавления в избранное."""

        request = self.context.get('request')
        return RecipeSerializerBrief(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Serializer модели ShoppingList."""

    class Meta:
        model = ShoppingList
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списоке покупок.'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializerBrief(
            instance.recipe,
            context={'request': request}
        ).data
