from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import TipoMantenimientoForm
from .models import TipoMantenimiento


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
