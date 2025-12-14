# finance/forms.py
from django import forms
from .models import Depense, Revenu
from projects.models import WorkCompletionRecord
# 'CustomUser' n'est plus nécessaire ici, mais 'Task' l'est
# from users.models import CustomUser 

class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        
        # 👇 CORRECTION: Ces champs correspondent maintenant à votre finance/models.py
        fields = [
            'date', 
            'projet_associe', 
            'site_concerne',
            'vehicule_concerne',
            'equipement_concerne',
            'categorie', 
            'description', 
            'montant', 
            'recu_scan'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        } 
        


class RevenuForm(forms.ModelForm):
    class Meta:
        model = Revenu
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        # Remarque : Votre template 'expense_list.html' affichait "Pays" et "Site".
        # Ces informations peuvent être récupérées via le champ 'projet_associe'
        # (car un Projet appartient à un Pays et contient des Sites).


class WorkCompletionForm(forms.ModelForm):
    class Meta:
        model = WorkCompletionRecord
        # Basé sur vos templates et signaux
        fields = [
            'date', 
            'employee', 
            'task', 
            'duration_hours', 
            'completion_percentage'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }