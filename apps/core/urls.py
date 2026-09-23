from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("buscar/", views.busqueda_global, name="search"),
]
