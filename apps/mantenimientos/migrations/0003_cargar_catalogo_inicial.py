from django.db import migrations


TIPOS_INICIALES = (
    "Cambio de aceite",
    "Filtro de aceite",
    "Filtro de aire",
    "Bujías",
    "Pastillas de freno",
    "Líquido de freno",
    "Líquido refrigerante",
    "Cadena / transmisión",
    "Cubiertas",
    "Batería",
    "Service general",
)


def cargar_catalogo_inicial(apps, schema_editor):
    TipoMantenimiento = apps.get_model("mantenimientos", "TipoMantenimiento")
    for nombre in TIPOS_INICIALES:
        TipoMantenimiento.objects.get_or_create(
            nombre=nombre,
            defaults={"activo": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("mantenimientos", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(cargar_catalogo_inicial, migrations.RunPython.noop),
    ]
