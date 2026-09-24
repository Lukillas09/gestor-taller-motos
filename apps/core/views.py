from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.motos.models import Moto
from apps.notificaciones.services import obtener_resumen_seguimientos
from apps.servicios.models import Servicio


@login_required
def dashboard(request):
    resumen_seguimientos = obtener_resumen_seguimientos()
    resumen_alertas = resumen_seguimientos.resumen_tecnico
    cards = [
        {
            "label": "Mantenimientos vencidos",
            "value": len(resumen_alertas.vencidos),
            "tone": "danger",
            "url": f'{reverse("notificaciones:alertas")}?estado=VENCIDO&seguimiento=todos',
        },
        {
            "label": "Próximos mantenimientos",
            "value": len(resumen_alertas.proximos),
            "tone": "warning",
            "url": f'{reverse("notificaciones:alertas")}?estado=PROXIMO&seguimiento=todos',
        },
        {
            "label": "Clientes",
            "value": Cliente.objects.filter(activo=True).count(),
            "tone": "primary",
            "url": reverse("clientes:list"),
        },
        {
            "label": "Motos",
            "value": Moto.objects.filter(activo=True).count(),
            "tone": "success",
            "url": reverse("motos:list"),
        },
    ]
    ultimos_servicios = Servicio.objects.con_detalle()[:5]
    return render(
        request,
        "core/dashboard.html",
        {
            "cards": cards,
            "resumen_alertas": resumen_alertas,
            "resumen_seguimientos": resumen_seguimientos,
            "alertas_prioritarias": resumen_seguimientos.accionables[:5],
            "ultimos_servicios": ultimos_servicios,
        },
    )


@login_required
def busqueda_global(request):
    termino = request.GET.get("q", "").strip()
    clientes = Cliente.objects.none()
    motos = Moto.objects.none()

    if termino:
        clientes = (
            Cliente.objects.filter(activo=True)
            .buscar(termino)
            .annotate(
                cantidad_motos=Count(
                    "motos", filter=Q(motos__activo=True), distinct=True
                )
            )[:8]
        )
        motos = (
            Moto.objects.filter(activo=True)
            .select_related("cliente")
            .buscar(termino)[:8]
        )

    return render(
        request,
        "core/search.html",
        {"termino": termino, "clientes": clientes, "motos": motos},
    )
