from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.motos.models import Moto


@login_required
def dashboard(request):
    cards = [
        {"label": "Mantenimientos vencidos", "value": 0, "tone": "danger"},
        {"label": "Próximos mantenimientos", "value": 0, "tone": "warning"},
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
    return render(request, "core/dashboard.html", {"cards": cards})


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
