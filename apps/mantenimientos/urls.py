from django.urls import path

from . import views


app_name = "mantenimientos"

urlpatterns = [
    path("configuracion/", views.configuracion_list, name="configuracion"),
    path("configuracion/nuevo/", views.tipo_create, name="tipo_create"),
    path(
        "configuracion/<int:pk>/editar/",
        views.tipo_update,
        name="tipo_update",
    ),
    path(
        "configuracion/<int:pk>/desactivar/",
        views.tipo_archive,
        name="tipo_archive",
    ),
    path(
        "configuracion/<int:pk>/restaurar/",
        views.tipo_restore,
        name="tipo_restore",
    ),
]
