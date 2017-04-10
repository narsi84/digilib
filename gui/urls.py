from django.conf.urls import include, url
from django.views.generic.base import TemplateView

from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'books', views.BookViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'categories', views.CategoryViewSet)


urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/scan', views.scan, name='scan'),
    url(r'^api/v1/createBook', views.createBook, name='createBook'),
    url(r'^api/v1/startBook', views.startBook, name='startBook'),
    url(r'^api/v1/stopBook', views.stopBook, name='stopBook'),
    url(r'^api/v1/test', views.test, name='test'),
    url(r'^api/v1/autoScan', views.auto_scan, name='auto_scan'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
