# users/forms.py (VERSION FINALE ET CORRIGÉE)

from django import forms
from .models import CustomUser, EmployeeDocument, Country
from django_countries.fields import CountryField
from phonenumber_field.formfields import PhoneNumberField
import phonenumbers

class EmployeeCreateForm(forms.ModelForm):
    hire_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    nationality = CountryField().formfield(required=False)
    assigned_countries = forms.ModelMultipleChoiceField(
        queryset=Country.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'department', 'contract_type',
            'hire_date', 'job_role', 'nationality', 'assigned_countries'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'] = forms.CharField(
            widget=forms.PasswordInput,
            initial='Newntc@25',
            required=True
        )
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            self.save_m2m()
        return user

class ProfileUpdateForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'datepicker'}),
        required=False
    )
    nationality = CountryField().formfield(required=False)
    birth_country = CountryField().formfield(required=False)
    phone_number_display = forms.CharField(
        required=False,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'class': 'phone-number form-control',
            'id': 'id_phone_number',
        })
    )

    class Meta:
        model = CustomUser
        # On enlève 'phone_number' car on le gère manuellement
        fields = [
            'first_name', 'last_name', 'other_first_name', 'email', 'birth_date',
            'nationality', 'birth_country', 'blood_group', 'address',
            'id_type', 'id_number', 'professional_email', 'allergies',
            'recurring_illness', 'special_allergies', 'isignum_number', 'eritop_id',
            'bank', 'bank_account_number', 'social_security_number', 'profile_picture'
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'other_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recurring_illness': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'special_allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'isignum_number': forms.TextInput(attrs={'class': 'form-control'}),
            'eritop_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'social_security_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.phone_number:
            self.fields['phone_number_display'].initial = str(self.instance.phone_number)

        self.fields['professional_email'].label = "Adresse email professionnelle"
        self.fields['id_number'].label = "Numéro de la pièce d'identité"
        self.fields['bank_account_number'].label = "Numéro de compte bancaire"
        self.fields['social_security_number'].label = "Numéro de sécurité sociale"
        self.fields['professional_email'].widget.attrs['placeholder'] = "prenom.nom@entreprise.com"

    def clean(self):
        cleaned_data = super().clean()
        raw_number = cleaned_data.get('phone_number_display')

        # Si le champ est vide, on s'assure que le numéro de modèle est aussi vide.
        if not raw_number:
            cleaned_data['phone_number'] = None
            return cleaned_data

        raw_number = raw_number.strip()
        
        # Le front-end (intl-tel-input) est censé TOUJOURS envoyer un numéro avec '+'
        # S'il n'y en a pas, c'est un fallback ou un problème JS.
        # On choisit de forcer le Bénin (BJ) par défaut dans ce cas.
        if not raw_number.startswith('+'):
            try:
                # On suppose que c'est un numéro local (Bénin)
                parsed_number = phonenumbers.parse(raw_number, "BJ")
            except phonenumbers.NumberParseException:
                self.add_error('phone_number_display', "Format du numéro de téléphone invalide.")
                return cleaned_data # On arrête ici
        else:
            try:
                # Le numéro a déjà un indicatif
                parsed_number = phonenumbers.parse(raw_number, None)
            except phonenumbers.NumberParseException:
                self.add_error('phone_number_display', "Format du numéro de téléphone invalide.")
                return cleaned_data # On arrête ici

        # On utilise la validation la moins stricte pour accepter plus de numéros
        if not phonenumbers.is_possible_number(parsed_number):
            self.add_error('phone_number_display', "Le numéro de téléphone ne semble pas correct (vérifiez la longueur).")
        else:
            # Si tout va bien, on stocke le numéro au format E.164 dans le champ du modèle
            cleaned_data['phone_number'] = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            
        return cleaned_data


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'document']
        widgets = {
            'document_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CV, Contrat, Diplôme...'
            }),
            'document': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'document_type': "Type de document",
            'document': "Fichier"
        }
        help_texts = {
            'document': "Téléchargez le document (PDF, Word, Image, etc.)"
        }

    def clean_document(self):
        document = self.cleaned_data.get('document')
        if document:
            if document.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Le fichier est trop volumineux. Taille maximale: 10MB.")

            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt']
            if not any(document.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError(
                    "Type de fichier non supporté. Formats autorisés: PDF, Word, JPG, PNG, TXT."
                )
        return document