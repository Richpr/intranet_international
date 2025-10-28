from django import forms
from .models import Certification, PaiementSalaire

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = '__all__'
        widgets = {
            'date_expiration': forms.DateInput(attrs={'type': 'date'}),
        }

class PaiementSalaireForm(forms.ModelForm):
    class Meta:
        model = PaiementSalaire
        fields = '__all__'
