# config/urls.py

from django.contrib import admin
from django.urls import path, include
from core.views import HomeView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    # Ajoutez les URLs d'authentification (connexion, déconnexion, etc.)
    path("accounts/", include("django.contrib.auth.urls")),
    path("projects/", include("projects.urls")),
    path("finance/", include("finance.urls")),
    path("reporting/", include("reporting.urls")),
    path("", HomeView.as_view(), name="home"),
]

# AJOUTEZ cette ligne à la fin
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
