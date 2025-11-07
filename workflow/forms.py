from django import forms
from .models import PermissionRequest

class PermissionRequestForm(forms.ModelForm):
    class Meta:
        model = PermissionRequest
        fields = ['request_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
