from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from .views import (
    AuthViewSet, LocationViewSet, CategoryViewSet,
    TicketViewSet, AttachmentViewSet, ReportViewSet
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'locations', LocationViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'tickets', TicketViewSet)
router.register(r'attachments', AttachmentViewSet)
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
