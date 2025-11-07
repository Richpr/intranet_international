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
    path("inventaire/", include("inventaire.urls", namespace="inventaire")),
    path("logistique/", include("logistique.urls", namespace="logistique")),
    path('rh/', include('rh.urls')),
    path('data-analytics/', include('data_analytics.urls')),
    path('workflow/', include('workflow.urls', namespace='workflow')),
    path('documentation/', include('documentation.urls', namespace='documentation')),
    path("", HomeView.as_view(), name="home"),
    # 👇 AJOUTE ÇA :
    # Fait de l'app 'core' la page d'accueil du site
    path("", include("core.urls", namespace="core")),
]

# AJOUTEZ cette ligne à la fin
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
