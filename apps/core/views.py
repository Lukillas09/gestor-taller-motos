from django.shortcuts import render


def dashboard(request):
    cards = [
        {"label": "Mantenimientos vencidos", "value": 0, "tone": "danger"},
        {"label": "Proximos mantenimientos", "value": 0, "tone": "warning"},
        {"label": "Clientes", "value": 0, "tone": "primary"},
        {"label": "Motos", "value": 0, "tone": "success"},
    ]
    return render(request, "core/dashboard.html", {"cards": cards})
