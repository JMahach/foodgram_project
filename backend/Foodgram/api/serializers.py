from recipes.models import Amount, Ingredient, Recipe, Tag, User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class TagSerializer(serializers.ModelSerializer):
    """Serializer для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class TagDifferentInOut(serializers.RelatedField):
    """Serializer для связанного поля Tag."""

    def to_representation(self, instance):
        return TagSerializer(instance).data

    def to_internal_value(self, data):
        try:
            obj = Tag.objects.get(pk=data)
            return obj
        except Tag.DoesNotExist:
            raise serializers.ValidationError(
                'Тэга не существует'
            )


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'


# class AmountSerializer(serializers.ModelSerializer):
#     """Serializer для модели Ingredient."""

#     id = serializers.PrimaryKeyRelatedField(
#         queryset=Ingredient.objects.all(),
#     )

#     class Meta:
#         model = Amount
#         fields = ['id', 'amount']
#         extra_kwargs = {
#             'amount': {'required': True},
#             'recipe': {'required': False},
#         }


class IngredientDifferentInOut(serializers.RelatedField):
    """Serializer для связанного поля Tag."""

    def to_representation(self, instance):
        data = IngredientSerializer(instance).data
        return data

    def to_internal_value(self, data):
        try:
            obj = Ingredient.objects.get(pk=data['id'])
            return {'ingredient': obj, 'amount': data['amount']}
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                'Ингредиента не существует'
            )


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer для модели Recipe."""

    # author = UserSerializer(read_only=True)
    tags = TagDifferentInOut(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientDifferentInOut(
        queryset=Amount.objects.all(),
        many=True,
    )

    class Meta:
        model = Recipe
        fields = '__all__'

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
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

    # update


class RecipeSerializerRead():
    pass
