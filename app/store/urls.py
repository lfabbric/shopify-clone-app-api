from django.urls import path, include
from rest_framework.routers import DefaultRouter

from store import views


router = DefaultRouter()
router.register('stores', views.StoreViewSet)
product_list = views.ProductViewSet.as_view({'get': 'list'})
product_detail = views.ProductViewSet.as_view({'get': 'retrieve'})
collection_list = views.CollectionViewSet.as_view({'get': 'list'})
collection_product_list = views.CollectionViewSet.as_view(
    {'get': 'product_list'}
)

app_name = 'store'

urlpatterns = [
    path('', include(router.urls)),
    path('<slug:slug>/products/', product_list, name='product-list'),
    path(
        '<slug:slug>/products/<int:pk>',
        product_detail,
        name='product-detail'
    ),
    path('<slug:slug>/collections/', collection_list, name='collection-list'),
    path(
        '<slug:store>/collections/<int:pk>/products',
        collection_product_list,
        name='collection-product-list',
    ),
]
