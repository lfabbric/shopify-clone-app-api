from django.urls import path, include
from rest_framework.routers import DefaultRouter

from commerce import views


app_name = 'commerce'

router = DefaultRouter()
router.register(f'{app_name}/shippings', views.ShippingViewSet)
router.register(f'{app_name}/orders', views.CustomerOrderViewSet)
router.register(f'{app_name}/carts', views.CartViewSet)
router.register(f'admin/{app_name}/order', views.StoreOwnerOrderViewSet)

urlpatterns = [
    path(
        '<slug:store>/', include(router.urls),
    ),
]
