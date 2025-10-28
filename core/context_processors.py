# core/context_processors.py
from users.models import Country  # AJOUTER CET IMPORT


def roles_and_permissions(request):
    """
    Ajoute les variables de rôle à tous les templates, en utilisant le modèle CustomUser.
    """
    user = request.user

    # Valeurs par défaut
    is_cm = False
    is_coordinator = False
    is_team_lead = False
    is_field_team = False
    is_finance = False

    if user.is_authenticated:
        # Utilise les propriétés du modèle CustomUser pour la cohérence
        is_cm = user.is_cm
        is_coordinator = user.is_coordinator
        is_team_lead = user.is_team_lead
        is_field_team = user.is_field_team

        # Logique Finance (vérifie si l'utilisateur a un rôle financier)
        user_roles = user.get_active_role_names()
        is_finance = (
            "Finance User" in user_roles
            or "Finance_Admin" in user_roles
            or "Finance User" in user_roles
        )

    has_finance_menu_access = is_cm or is_coordinator or is_finance

    return {
        # Ces booléens sont utilisés par les templates pour masquer/afficher des liens
        "is_cm": is_cm,
        "is_coordinator": is_coordinator,
        "is_team_lead": is_team_lead,
        "is_field_team": is_field_team,
        "is_finance_user": is_finance,
        "has_finance_menu_access": has_finance_menu_access,
    }


def user_countries_processor(request):
    """
    Ajoute la liste des pays de l'utilisateur à tous les templates.
    """
    user = request.user
    countries = []

    # 🟢 CORRECTION CRITIQUE : Initialiser active_country_ids
    active_country_ids = []

    if user.is_authenticated:
        # Utilise la propriété correcte
        active_country_ids = user.active_country_ids

        # Récupère les objets Country correspondants (en utilisant active_country_ids)
        countries = Country.objects.filter(id__in=active_country_ids)

    return {
        "user_countries": countries,
        "active_country_ids": active_country_ids,  # Cette variable est maintenant toujours définie
    }
