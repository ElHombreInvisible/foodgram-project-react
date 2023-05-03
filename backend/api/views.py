from http import HTTPStatus

from django.db import transaction
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, IngredientModel, RecipeIngredients,
                            RecipeModel, TagModel)

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import AdminOrOwnerOrReadOnly
from .serializers import (CreateIngredientAmountSerializer,
                          CreateRecipeTagsSerializer, IngredientSerializer,
                          PostRecipeSerializer, RecipeSerializer,
                          TagSerializer)
from .utils import create_pdf


class TagViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.RetrieveModelMixin):

    queryset = TagModel.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin):

    queryset = IngredientModel.objects.all()
    serializer_class = IngredientSerializer
    filterset_fields = ('name',)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.GenericViewSet,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin):

    queryset = RecipeModel.objects.all()
    permission_classes = (AdminOrOwnerOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

    def perform_destroy(self, instance):
        if instance.image is not None:
            instance.image.delete()
        return super().perform_destroy(instance)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return PostRecipeSerializer
        return RecipeSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        tags = serializer.initial_data.pop('tags')
        ingredients = {}
        ingredients['ingredients'] = serializer.initial_data.pop('ingredients')
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        tagserializer = CreateRecipeTagsSerializer(data={'id': tags},
                                                   context=serializer.instance)
        tagserializer.is_valid(raise_exception=True)
        tagserializer.save()
        ingredients_serializer = CreateIngredientAmountSerializer(
                                       data=ingredients,
                                       context=serializer.instance)

        ingredients_serializer.is_valid(raise_exception=True)
        ingredients_serializer.save()
        recipe = RecipeSerializer(serializer.instance,
                                  context={'request': request})
        return Response(recipe.data, status=HTTPStatus.CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        recipe = RecipeModel.objects.filter(pk=kwargs['pk']).first()
        serializer = self.get_serializer(data=request.data)
        tags = serializer.initial_data.pop('tags')
        tagserializer = CreateRecipeTagsSerializer(data={'id': tags},
                                                   context=recipe)
        tagserializer.is_valid(raise_exception=True)
        tagserializer.update(instance=recipe,
                             validated_data=tagserializer.data)
        ingredients = {}
        ingredients['ingredients'] = serializer.initial_data.pop('ingredients')
        ingredients_serializer = CreateIngredientAmountSerializer(
                                       data=ingredients,
                                       context=recipe)
        ingredients_serializer.is_valid(raise_exception=True)
        ingredients_serializer.update(
            validated_data=ingredients_serializer.data,
            instance=recipe
            )
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=recipe,
                          validated_data=serializer.validated_data)
        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=HTTPStatus.OK)

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, context, pk=None):
        recipe_qs = RecipeModel.objects.filter(pk=pk)
        if not recipe_qs.exists():
            return Response({'errors': 'Рецепта не существует'},
                            status=HTTPStatus.NOT_FOUND)
        recipe = recipe_qs.first()
        in_favorite = FavoriteRecipe.objects.filter(user=context.user,
                                                    recipe=recipe)
        if context.method == 'POST':
            if in_favorite.exists():
                return Response({'errors': 'рецепт уже в любимых'},
                                status=HTTPStatus.BAD_REQUEST)
            FavoriteRecipe.objects.create(user=context.user,
                                          recipe=recipe)
            data = {
                'id': recipe.id,
                'name': recipe.name,
                'image': self.request.build_absolute_uri(recipe.image.url),
                'cooking_time': recipe.cooking_time,
                    }
            return Response(data=data, status=HTTPStatus.CREATED)
        else:
            if not in_favorite.exists():
                return Response(
                    {'errors': 'подписки на рецепт не существует'},
                    status=HTTPStatus.BAD_REQUEST
                    )
            in_favorite.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,),
            url_name='download_shopping_cart',
            url_path='download_shopping_cart')
    def download_shopping_cart(self, context, pk=None):
        template = 'shopping_list.html'
        ingredients = RecipeIngredients.objects.values(
            'ingredients__name', 'ingredients__measurement_unit').annotate(
                sum_amount=Sum('amount')).filter(
                    recipe__favoring_users__user=context.user)
        context = {
            'ingredients': ingredients
        }
        page = render(request=self.request,
                      template_name=template,
                      context=context)
        file = create_pdf(page)
        return FileResponse(file,
                            filename='shopping_list.pdf',
                            content_type='application/pdf')
