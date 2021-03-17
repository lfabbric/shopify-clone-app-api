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
product_image_detail = views.ProductImageViewSet.as_view(
    {'get': 'retrieve'}
)
product_image_list = views.ProductImageViewSet.as_view(
    {'get': 'list'}
)
# clean up the default routers
product_router = DefaultRouter()
product_router.register('productimages', views.ProductImageViewSet)
product_router.register('productattachments', views.ProductAttachmentViewSet)

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
    path(
        '<slug:store>/', include(product_router.urls)
    ),
    path(
        '<slug:store>/', include(product_router.urls)
    ),
]
