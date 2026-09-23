from django.urls import path

from . import views


app_name = "motos"

urlpatterns = [
    path("", views.moto_list, name="list"),
    path("nueva/", views.moto_create, name="create"),
    path("<int:pk>/", views.moto_detail, name="detail"),
    path("<int:pk>/editar/", views.moto_update, name="update"),
    path("<int:pk>/archivar/", views.moto_archive, name="archive"),
    path("<int:pk>/restaurar/", views.moto_restore, name="restore"),
]
