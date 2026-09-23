from django.urls import path

from . import views


app_name = "servicios"

urlpatterns = [
    path("", views.servicio_list, name="list"),
    path("nuevo/", views.servicio_create, name="create"),
    path("contexto-moto/", views.moto_context, name="moto_context"),
    path("<int:pk>/", views.servicio_detail, name="detail"),
    path("<int:pk>/editar/", views.servicio_update, name="update"),
    path("<int:pk>/cancelar/", views.servicio_cancel, name="cancel"),
]
