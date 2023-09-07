from http import HTTPStatus

from django.db.models import OuterRef, Subquery, Prefetch
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import RecipeModel

from .models import Follow
from .pagination import PageLimitPagination
from .serializers import SubscribitionSerializer

User = get_user_model()


class UserViewSet(UserViewSet):

    @action(methods=["get"], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',
            url_name='subscribe',
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        following_qs = User.objects.filter(pk=id)
        if following_qs.exists():
            following = following_qs.first()
            follow = Follow.objects.filter(follower=request.user,
                                           author=following)
            if request.method == 'DELETE':
                if not follow.exists():
                    data = {'errors': 'Подписка не найдена'}
                    status = HTTPStatus.BAD_REQUEST
                else:
                    follow.delete()
                    status = HTTPStatus.NO_CONTENT
                    data = {'detail': 'Подписка отменена'}
            else:
                if request.user == following:
                    data = {'errors': 'Невозможно подписаться на самого себя.'}
                    status = HTTPStatus.BAD_REQUEST
                elif follow.exists():
                    data = {'errors': 'Подписка на автора уже существует.'}
                    status = HTTPStatus.BAD_REQUEST
                else:
                    Follow.objects.create(follower=request.user,
                                          author=following)
                    data = SubscribitionSerializer(
                        following,  # data = AuthorSerializer(following,
                        context={'request': request}).data
                    status = HTTPStatus.CREATED
        else:
            data = {'detail': 'Страница не найдена.'}
            status = HTTPStatus.NOT_FOUND
        return Response(data=data, status=status)


class SubscribitionViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,):

    serializer_class = SubscribitionSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = PageLimitPagination

    def get_queryset(self):
        recipes_limit = self.request.GET.get('recipes_limit', default=3)
        recipes_limit = int(recipes_limit)
        recipes = RecipeModel.objects.filter(author_id=OuterRef("author_id")
                                             )[:recipes_limit]
        return User.objects.filter(followed_by__follower=self.request.user
                                   ).prefetch_related(
             Prefetch("recipes",
                      queryset=RecipeModel.objects.filter(id__in=recipes)))
        #return User.objects.filter(followed_by__follower=self.request.user)
