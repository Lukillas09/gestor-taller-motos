from django.urls import path

from . import views


app_name = "notificaciones"

urlpatterns = [
    path("", views.alerta_list, name="alertas"),
    path(
        "<int:moto_pk>/<int:tipo_pk>/contactar/",
        views.contactar,
        name="contactar",
    ),
    path(
        "<int:moto_pk>/<int:tipo_pk>/posponer/",
        views.posponer,
        name="posponer",
    ),
    path(
        "<int:moto_pk>/<int:tipo_pk>/turno/",
        views.turno,
        name="turno",
    ),
    path(
        "<int:moto_pk>/<int:tipo_pk>/no-interesado/",
        views.no_interesado,
        name="no_interesado",
    ),
    path(
        "<int:moto_pk>/<int:tipo_pk>/reabrir/",
        views.reabrir,
        name="reabrir",
    ),
    path(
        "<int:moto_pk>/<int:tipo_pk>/nota/",
        views.nota,
        name="nota",
    ),
    path(
        "<int:moto_pk>/<int:tipo_pk>/historial/",
        views.historial,
        name="historial",
    ),
]
