from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.urls import include, path
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "service-worker.js",
        serve,
        {"path": "service-worker.js", "document_root": settings.BASE_DIR / "static"},
        name="service-worker",
    ),
    path("clientes/", include("apps.clientes.urls")),
    path("motos/", include("apps.motos.urls")),
    path("servicios/", include("apps.servicios.urls")),
    path("mantenimientos/", include("apps.mantenimientos.urls")),
    path("", include("apps.core.urls")),
]
