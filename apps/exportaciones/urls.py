from django.urls import path

from . import views


app_name = "exportaciones"

urlpatterns = [
    path("", views.index, name="index"),
    path("backup/", views.backup_instructions, name="backup_instructions"),
    path("clientes.csv", views.clientes_csv, name="clientes_csv"),
    path("motos.csv", views.motos_csv, name="motos_csv"),
    path("servicios.csv", views.servicios_csv, name="servicios_csv"),
    path(
        "mantenimientos.csv",
        views.mantenimientos_csv,
        name="mantenimientos_csv",
    ),
    path(
        "tipos-mantenimiento.csv",
        views.tipos_mantenimiento_csv,
        name="tipos_mantenimiento_csv",
    ),
    path("seguimientos.csv", views.seguimientos_csv, name="seguimientos_csv"),
    path(
        "eventos-seguimiento.csv",
        views.eventos_seguimiento_csv,
        name="eventos_seguimiento_csv",
    ),
    path("completo.xlsx", views.completo_xlsx, name="completo_xlsx"),
]
