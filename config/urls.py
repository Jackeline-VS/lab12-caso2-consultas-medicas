"""Rutas principales. Las rutas de la app se agregan al implementar las vistas."""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
