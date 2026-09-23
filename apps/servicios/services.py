from django.db import transaction

from apps.mantenimientos.models import MantenimientoRealizado


@transaction.atomic
def guardar_servicio_y_mantenimientos(
    servicio,
    tipos_mantenimiento,
    *,
    creado_por=None,
):
    if servicio._state.adding and creado_por and creado_por.is_authenticated:
        servicio.creado_por = creado_por

    servicio.save()

    tipos_ids = {tipo.pk for tipo in tipos_mantenimiento}
    realizaciones = MantenimientoRealizado.objects.filter(servicio=servicio)
    if tipos_ids:
        realizaciones.exclude(tipo_mantenimiento_id__in=tipos_ids).delete()
    else:
        realizaciones.delete()

    existentes = set(
        realizaciones.filter(tipo_mantenimiento_id__in=tipos_ids).values_list(
            "tipo_mantenimiento_id", flat=True
        )
    )
    MantenimientoRealizado.objects.bulk_create(
        [
            MantenimientoRealizado(
                servicio=servicio,
                tipo_mantenimiento_id=tipo_id,
            )
            for tipo_id in tipos_ids - existentes
        ]
    )
    return servicio
