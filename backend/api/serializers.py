from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField
from rest_framework.validators import ValidationError

from recipes.models import (FavoriteRecipe, IngredientModel, RecipeIngredients,
                            RecipeModel,  ShoppingCartRecipes,
                            TagModel)
from users.models import Follow, User

from .serializer_fields import Base64ImageField


RecipeTag = RecipeModel.tags.through


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagModel
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientModel
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredients.id')
    name = serializers.CharField(source='ingredients.name')
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit')

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField('get_subscription')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_subscription(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Follow.objects.filter(follower=self.context['request'].user,
                                     author=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountSerializer(many=True,
                                             source='recipe_ingredients')
    is_favorited = SerializerMethodField('get_is_favorited')
    is_in_shopping_cart = SerializerMethodField('get_is_in_shopping_cart')

    class Meta:
        model = RecipeModel
        fields = ('id', 'tags', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'author',  'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(user=self.
                                             context['request'].user,
                                             recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return ShoppingCartRecipes.objects.filter(user=self.
                                                  context['request'].user,
                                                  recipe=obj).exists()


class FavoriteRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeModel
        fields = ('id', 'name', 'image', 'cooking_time')


class CreateIngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=IngredientModel.objects.all(),
        )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class PostRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(allow_null=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=TagModel.objects.all(), many=True
        )
    ingredients = CreateIngredientAmountSerializer(many=True,
                                                   source='recipe_ingredients')

    class Meta:
        model = RecipeModel
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time',)

    @transaction.atomic
    def create(self, validated_data):
        author = self.context['request'].user
        tags = validated_data.pop('tags')
        ingredietns = validated_data.pop('recipe_ingredients')
        recipe = RecipeModel.objects.create(**validated_data,
                                            author=author)
        for elem in ingredietns:
            RecipeIngredients.objects.create(ingredients=elem['id'],
                                             recipe=recipe,
                                             amount=elem['amount'])
        for tag in tags:
            RecipeTag.objects.create(recipemodel=recipe, tagmodel=tag)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredietns = validated_data.pop('recipe_ingredients')
        if instance.image is not None:
            instance.image.delete()
        for elem in ingredietns:
            defaults = {'amount': elem['amount']}
            RecipeIngredients.objects.update_or_create(
                ingredients=elem['id'],
                recipe=instance,
                defaults=defaults)
        ingredients = [x['id'] for x in ingredietns]
        RecipeIngredients.objects.filter(
            ~Q(ingredients__in=ingredients),
            recipe=instance
            ).delete()
        for tag in tags:
            RecipeTag.objects.get_or_create(recipemodel=instance, tagmodel=tag)
        RecipeTag.objects.filter(~Q(tagmodel__in=tags),
                                 recipemodel=instance).delete()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        new = RecipeSerializer(instance, context=self.context)
        return new.data

    def validate_ingredients(self, obj):
        if obj == []:
            raise ValidationError("Ingredients list must not be empty")
        return obj

    def validate_tags(self, obj):
        if obj == []:
            raise ValidationError("Tags list must not be empty")
        return obj
