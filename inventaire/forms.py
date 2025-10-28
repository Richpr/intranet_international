from django import forms
from .models import Equipement, AllocationEquipement

class EquipementForm(forms.ModelForm):
    class Meta:
        model = Equipement
        fields = '__all__'
        widgets = {
            'date_prochaine_inspection': forms.DateInput(attrs={'type': 'date'}),
        }

class AllocationEquipementForm(forms.ModelForm):
    class Meta:
        model = AllocationEquipement
        fields = '__all__'
