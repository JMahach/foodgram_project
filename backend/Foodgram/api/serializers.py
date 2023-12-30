from django.db import transaction
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator


from api.utils import Base64ImageField
from recipes.models import (Amount, Favorite, Ingredient,
                            Recipe, ShoppingList, Tag)
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

    def validate(self, obj):
        """Валидация поля username."""
        if self.initial_data.get('username').lower() == 'me':
            me = "'me'"
            raise serializers.ValidationError(
                {'username': f'Имя пользователя не может быть {me}.'}
            )
        return obj

    def to_representation(self, instance):
        """Логика ответа после создания Пользователя."""
        request = self.context.get('request')
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name'
        ]
        data = UserSerializerRead(
            instance,
            context={'request': request}
        ).data
        filtered_data = {key: data[key] for key in fields}
        return filtered_data


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
        return (request.user.is_authenticated and
                Subscription.objects.filter(
                    user=request.user,
                    author=obj
                ).exists())


class UserSerializerSubscripe(UserSerializerRead):
    """"
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
            recipes_limit = recipes_limit.rstrip(',')
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


class IngredientDiffIn(serializers.RelatedField):
    """Serializer для связанного поля ingredients."""

    def to_internal_value(self, data):
        """Обработка данных поля ingredients"""
        try:
            ingredient = Ingredient.objects.get(pk=data['id'])
            return {'ingredient': ingredient, 'amount': data['amount']}
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                {'id': 'Ингредиента не существует.'}
            )
        except KeyError as e:
            raise serializers.ValidationError(
                {str(e).replace("'", ""): 'Обязательное поле.'}
            )


class RecipeSerializerWrite(serializers.ModelSerializer):
    """Serializer модели Recipe для записи."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientDiffIn(
        queryset=Amount.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        """Валидация полей."""
        errors = {}
        ingredients = set()
        for ingredient in data.get('ingredients', []):
            if int(ingredient.get('amount')) < 1:
                errors['ingredients'] = {
                    'amount': 'Количество должно быть больше 0'
                }
            if ingredient['ingredient'].id in ingredients:
                errors['ingredients'] = {
                    'ingredient':
                    'Вы пытаетесь добавить в рецепт два одинаковых ингредиента'
                }
            ingredients.add(ingredient['ingredient'].id)

        if not data.get('tags'):
            errors['tags'] = 'Необходимо указать хотябы 1 тег.'
        if not data.get('ingredients'):
            errors['ingredients'] = 'Необходимо указать хотябы 1 ингридиент.'

        if errors:
            raise serializers.ValidationError(errors)

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Сохранение Рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            Amount.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Изменение Рецепта."""

        tags_data = validated_data.get('tags', instance.tags.all())
        instance.tags.set(tags_data)
        instance.author = instance.author
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)

        if 'ingredients' in validated_data:
            ingredients_data = validated_data.get('ingredients')
            instance.amounts.all().delete()
            instance.save()

            for ingredient_data in ingredients_data:
                Amount.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data['ingredient'],
                    amount=ingredient_data['amount']
                )
        else:
            instance.save()
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
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        """Добавялет в поле Ингридиета его вес."""
        amounts = Amount.objects.filter(recipe=obj)
        ingredients_data = []
        for amount in amounts:
            ingredient_data = IngredientSerializer(amount.ingredient).data
            ingredient_data['amount'] = amount.amount
            ingredients_data.append(ingredient_data)
        return ingredients_data

    def get_is_favorited(self, obj):
        """
        Добавляет в ответ булево поле добавлен ли
        рецепт в избранное текущего пользователя.
        """
        request = self.context.get('request')
        return (request.user.is_authenticated and
                obj.favorites.filter(user=request.user.id).exists())

    def get_is_in_shopping_cart(self, obj):
        """
        Добавляет в ответ булево поле добавлен ли
        рецепт в список покпок текущего пользователя.
        """
        request = self.context.get('request')
        return (request.user.is_authenticated and
                obj.shopping_list.filter(user=request.user.id).exists())


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
