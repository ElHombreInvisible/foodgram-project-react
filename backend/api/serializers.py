from django.db.models import Q
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField
from rest_framework.validators import ValidationError

from recipes.models import (FavoriteRecipe, IngredientModel, RecipeIngredients,
                            RecipeModel, RecipeTag, ShoppingCartRecipes,
                            TagModel)
from users.models import Follow, User

from .serializer_fields import Base64ImageField


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
    amount = serializers.IntegerField()
    measurement_unit = serializers.CharField(
        source='ingredients.measurement_unit')

    class Meta:
        model = IngredientModel
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


class CreateRecipeTagsSerializer(serializers.ModelSerializer):
    id = serializers.ListField(required=True)

    class Meta:
        model = RecipeTag
        fields = ('id',)

    def create(self, validated_data):
        for tag_id in validated_data['id']:
            tag = TagModel.objects.filter(id=tag_id)
            if not tag.exists():
                raise ValidationError({'detail': 'tag does not exist'})
            RecipeTag.objects.create(recipe=self.context,
                                     tags=tag.first())
        return validated_data

    def update(self, instance, validated_data):
        tags = validated_data['id']
        for tag_id in tags:
            tag = TagModel.objects.filter(id=tag_id)
            RecipeTag.objects.get_or_create(recipe=instance,
                                            tags=tag.first())
        RecipeTag.objects.filter(~Q(tags__in=tags),
                                 recipe=instance).delete()
        return None

    def validate_id(self, obj):
        if obj == []:
            raise ValidationError("field 'tags' is required")
        tags_count = TagModel.objects.filter(id__in=obj).count()
        if len(obj) != tags_count:
            raise ValidationError('tag does not exist')
        return obj


class CreateIngredientAmountSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(required=True)

    class Meta:
        model = RecipeIngredients
        fields = ('ingredients',)

    def create(self, validated_data):
        ingredient_amount = validated_data['ingredients']
        for elem in ingredient_amount:
            ingredient = IngredientModel.objects.get(id=elem['id'])
            RecipeIngredients.objects.create(ingredients=ingredient,
                                             recipe=self.context,
                                             amount=elem['amount'])
        return validated_data

    def update(self, instance, validated_data):
        ingredients = validated_data.get('ingredients')
        for ingredient in ingredients:
            ingredient_instance = IngredientModel.objects.get(
                id=ingredient['id']
                )
            defaults = {'amount': ingredient['amount']}
            RecipeIngredients.objects.update_or_create(
                ingredients=ingredient_instance,
                recipe=instance,
                defaults=defaults,
                )
        ingredients_id = [instance.get('id') for instance in ingredients]
        RecipeIngredients.objects.filter(
            ~Q(ingredients__id__in=ingredients_id),
            recipe=instance
            ).delete()
        return validated_data

    def validate_ingredients(self, obj):
        if obj == []:
            raise ValidationError("Ingredients list must not be empty")
        ingredient_id = [instance.get('id') for instance in obj]
        ingredients = IngredientModel.objects.filter(
            id__in=ingredient_id
            ).count()
        if len(obj) != ingredients:
            raise ValidationError({'detail': 'ingredient does not exist'})
        return obj


class PostRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(allow_null=True, required=True)

    class Meta:
        model = RecipeModel
        fields = ('name', 'text', 'cooking_time', 'image')

    def create(self, validated_data):
        author = self.context['request'].user
        recipe = RecipeModel.objects.create(**validated_data,
                                            author=author)
        return recipe

    def update(self, instance, validated_data):
        if instance.image is not None:
            instance.image.delete()
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def validate_name(self, obj):
        if len(obj) == 0:
            raise ValidationError("Name field must not be empty")
        return obj

    def validate_text(self, obj):
        if len(obj) == 0:
            raise ValidationError("Text field must not be empty")
        return obj

    def validate_cooking_time(self, obj):
        if obj < 1:
            raise ValidationError("Cooking time must be postitive integer")
        return obj
