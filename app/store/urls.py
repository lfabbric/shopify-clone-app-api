from rest_framework_nested import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from store import views

app_name = 'store'

store_router = DefaultRouter()
store_router.register('stores', views.StoreViewSet)

router = routers.SimpleRouter()
router.register(f'{app_name}/products', views.ProductViewSet)
router.register(f'{app_name}/collections', views.CollectionViewSet)

related_router = routers.NestedSimpleRouter(
    router,
    f'{app_name}/products',
    lookup='product'
)
related_router.register(
    r'productimages',
    views.ProductImageViewSet,
    basename='product-images'
)
related_router.register(
    r'productattachments',
    views.ProductAttachmentViewSet,
    basename='product-attachments'
)

urlpatterns = [
    path('', include(store_router.urls),),
    path('<slug:store>/', include(router.urls),),
    path('<slug:store>/', include(related_router.urls),),
]
