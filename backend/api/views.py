from http import HTTPStatus

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, IngredientModel, RecipeIngredients,
                            RecipeModel, ShoppingCartRecipes, TagModel)

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import AdminOrOwnerOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          PostRecipeSerializer, RecipeSerializer,
                          TagSerializer)
from .utils import create_pdf


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = TagModel.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = IngredientModel.objects.all()
    serializer_class = IngredientSerializer
    filterset_fields = ('name',)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):

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
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return PostRecipeSerializer
        return RecipeSerializer

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, context, pk=None):
        recipe = get_object_or_404(RecipeModel, pk=pk)
        in_favorite = FavoriteRecipe.objects.filter(user=context.user,
                                                    recipe=recipe)
        if context.method == 'POST':
            if in_favorite.exists():
                return Response({'errors': 'рецепт уже в любимых'},
                                status=HTTPStatus.BAD_REQUEST)
            FavoriteRecipe.objects.create(user=context.user,
                                          recipe=recipe)
            serializer = FavoriteRecipeSerializer(
                recipe,
                context={'request': context}
                )
            return Response(data=serializer.data, status=HTTPStatus.CREATED)
        else:
            if not in_favorite.exists():
                return Response(
                    {'errors': 'подписки на рецепт не существует'},
                    status=HTTPStatus.BAD_REQUEST
                    )
            in_favorite.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, context, pk=None):
        recipe = get_object_or_404(RecipeModel, pk=pk)
        in_cart = ShoppingCartRecipes.objects.filter(user=context.user,
                                                     recipe=recipe)
        if context.method == 'POST':
            if in_cart.exists():
                return Response({'errors': 'рецепт уже в списках покупок'},
                                status=HTTPStatus.BAD_REQUEST)
            ShoppingCartRecipes.objects.create(user=context.user,
                                               recipe=recipe)
            serializer = FavoriteRecipeSerializer(
                recipe,
                context={'request': context}
                )
            return Response(data=serializer.data, status=HTTPStatus.CREATED)
        else:
            if not in_cart.exists():
                return Response(
                    {'errors': 'рецепт не в списке покупок'},
                    status=HTTPStatus.BAD_REQUEST
                    )
            in_cart.delete()
            return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,),
            url_name='download_shopping_cart',
            url_path='download_shopping_cart')
    def download_shopping_cart(self, context, pk=None):
        template = 'shopping_list.html'
        ingredients = RecipeIngredients.objects.values(
            'ingredients__name',
            'ingredients__measurement_unit'
            ).annotate(
                sum_amount=Sum('amount')).filter(
                    recipe__recipes_in_shopping_card__user=context.user
                    )
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
