from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                       UserSubscribeView, UserSubscribtionsListView)

app_name = 'api'


router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('users/subscriptions/',
         UserSubscribtionsListView.as_view(),
         name='subscriptions-list'),
    path('users/<int:user_id>/subscribe/', UserSubscribeView.as_view()),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls))
]
