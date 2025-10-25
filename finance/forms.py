# finance/forms.py

from django import forms
from .models import DailyExpense, WorkCompletionRecord
from projects.models import Site


class DailyExpenseForm(forms.ModelForm):

    class Meta:
        model = DailyExpense
        fields = ["country", "site", "date", "description", "amount"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # Récupère l'utilisateur passé par la vue
        super().__init__(*args, **kwargs)

        if user:
            # 1. Limiter les pays aux pays d'affectation de l'utilisateur
            active_country_ids = user.active_countries
            self.fields["country"].queryset = self.fields["country"].queryset.filter(
                id__in=active_country_ids
            )

            # 2. Limiter les sites aux sites qui appartiennent à ces pays
            # Le filtre passe par Site -> Project -> Country
            self.fields["site"].queryset = Site.objects.filter(
                project__country__id__in=active_country_ids
            )

        # Définir le pays par défaut si l'utilisateur n'a qu'une seule affectation
        if user and len(active_country_ids) == 1:
            self.fields["country"].initial = active_country_ids[0]


class WorkCompletionForm(forms.ModelForm):
    class Meta:
        model = WorkCompletionRecord
        # 1. CORRECTION: Remplacer 'user' par 'employee' dans les champs
        fields = ["task", "employee", "date", "duration_hours", "completion_percentage"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "task": forms.Select(attrs={"class": "form-control"}),
            # 2. CORRECTION: Remplacer 'user' par 'employee' dans les widgets
            "employee": forms.Select(attrs={"class": "form-control"}),
            "duration_hours": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Heures travaillées"}
            ),
            "completion_percentage": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Achèvement (%)"}
            ),
        }

    def __init__(self, *args, **kwargs):
        # ... (le reste de la logique est correct)
        country_id = kwargs.pop("country_id", None)
        super().__init__(*args, **kwargs)

        if country_id:
            # ... (Logique de filtrage des tâches)
            from projects.models import Task

            self.fields["task"].queryset = Task.objects.filter(
                site_task__site__project__country_id=country_id
            ).distinct()

            # 3. CORRECTION: Remplacer 'self.fields['user']' par 'self.fields['employee']'
            #    dans le filtrage du queryset
            from users.models import CustomUser

            self.fields["employee"].queryset = CustomUser.objects.filter(
                assignments__country_id=country_id, assignments__is_active=True
            ).distinct()
