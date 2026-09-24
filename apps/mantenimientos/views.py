import unicodedata

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.clientes.models import normalizar_telefono_busqueda
from apps.motos.models import normalizar_patente

from .forms import AlertasFiltroForm, TipoMantenimientoForm
from .models import TipoMantenimiento
from .services import obtener_resumen_alertas


def _normalizar_busqueda(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))


def _coincide_busqueda(alerta, termino):
    moto = alerta.moto
    cliente = moto.cliente
    contenido = _normalizar_busqueda(
        " ".join(
            (
                moto.patente or "",
                moto.marca,
                moto.modelo,
                cliente.nombre,
                cliente.apellido,
                cliente.telefono,
                alerta.tipo_mantenimiento.nombre,
            )
        )
    )
    patente = _normalizar_busqueda(moto.patente)
    telefono = normalizar_telefono_busqueda(cliente.telefono).casefold()
    for parte in _normalizar_busqueda(termino).split():
        if parte in contenido:
            continue
        patente_buscada = _normalizar_busqueda(normalizar_patente(parte))
        if patente_buscada and patente_buscada in patente:
            continue
        telefono_buscado = normalizar_telefono_busqueda(parte).casefold()
        if any(caracter.isdigit() for caracter in parte) and telefono_buscado:
            if telefono_buscado in telefono:
                continue
        return False
    return True


@login_required
def alerta_list(request):
    resumen = obtener_resumen_alertas()
    filtros = AlertasFiltroForm(
        request.GET or None,
        tipos_mantenimiento=resumen.tipos_configurados,
    )
    alertas = list(resumen.alertas)
    if filtros.is_valid():
        datos = filtros.cleaned_data
        if datos.get("estado"):
            alertas = [
                alerta
                for alerta in alertas
                if alerta.estado.value == datos["estado"]
            ]
        if datos.get("tipo"):
            alertas = [
                alerta
                for alerta in alertas
                if str(alerta.tipo_mantenimiento.pk) == datos["tipo"]
            ]
        if datos.get("q"):
            alertas = [
                alerta
                for alerta in alertas
                if _coincide_busqueda(alerta, datos["q"])
            ]

    contexto = {
        "alertas": alertas,
        "resumen": resumen,
        "filtros": filtros,
        "hay_filtros": any(
            request.GET.get(campo) for campo in ("q", "estado", "tipo")
        ),
    }
    if request.headers.get("HX-Request") == "true":
        return render(
            request,
            "mantenimientos/partials/lista_alertas.html",
            contexto,
        )
    return render(request, "mantenimientos/alertas.html", contexto)


@login_required
def configuracion_list(request):
    tipos = TipoMantenimiento.objects.order_by("-activo", "nombre", "pk")
    return render(
        request,
        "mantenimientos/configuracion.html",
        {"tipos": tipos},
    )


@login_required
def tipo_create(request):
    form = TipoMantenimientoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tipo = form.save()
        messages.success(request, "Tipo de mantenimiento creado correctamente.")
        return redirect("mantenimientos:tipo_update", pk=tipo.pk)
    return render(
        request,
        "mantenimientos/form.html",
        {
            "form": form,
            "titulo": "Nuevo tipo de mantenimiento",
            "texto_boton": "Crear mantenimiento",
        },
    )


@login_required
def tipo_update(request, pk):
    tipo = get_object_or_404(TipoMantenimiento, pk=pk)
    form = TipoMantenimientoForm(request.POST or None, instance=tipo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Configuración de mantenimiento actualizada.")
        return redirect("mantenimientos:configuracion")
    return render(
        request,
        "mantenimientos/form.html",
        {
            "form": form,
            "tipo": tipo,
            "titulo": "Editar mantenimiento",
            "texto_boton": "Guardar configuración",
        },
    )


@login_required
@require_POST
def tipo_archive(request, pk):
    tipo = get_object_or_404(TipoMantenimiento, pk=pk, activo=True)
    tipo.activo = False
    tipo.save(update_fields=("activo", "actualizado_en"))
    messages.success(request, "Tipo de mantenimiento desactivado.")
    return redirect("mantenimientos:configuracion")


@login_required
@require_POST
def tipo_restore(request, pk):
    tipo = get_object_or_404(TipoMantenimiento, pk=pk, activo=False)
    tipo.activo = True
    tipo.save(update_fields=("activo", "actualizado_en"))
    messages.success(request, "Tipo de mantenimiento restaurado.")
    return redirect("mantenimientos:configuracion")
