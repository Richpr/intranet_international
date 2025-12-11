# users/forms.py (VERSION CORRIGÉE)

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, EmployeeDocument, Country
from django_countries.fields import CountryField
from phonenumber_field.formfields import PhoneNumberField
import phonenumbers


class EnhancedLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre nom d\'utilisateur',
            'autocomplete': 'username',
            'autofocus': True,
            'spellcheck': 'false',
            'id': 'id_username_login',
        }),
        label=_("Nom d'utilisateur")
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
            'spellcheck': 'false',
            'id': 'id_password_login',
        }),
        label=_("Mot de passe")
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label=_("Se souvenir de moi")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for password field
        self.fields['password'].help_text = _(
            "Assurez-vous d'utiliser le mot de passe correct"
        )


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
            widget=forms.PasswordInput(attrs={'class': 'form-control'}),
            initial='Newntc@25',
            required=True
        )
        
        # Ajouter des placeholders pour une meilleure UX
        self.fields['email'].widget.attrs['placeholder'] = 'exemple@entreprise.com'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Prénom'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Nom'
        
        for field_name, field in self.fields.items():
            if field_name != 'assigned_countries':  # CheckboxSelectMultiple n'a pas besoin de form-control
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
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control datepicker'}),
        required=False
    )
    nationality = CountryField().formfield(required=False)
    birth_country = CountryField().formfield(required=False)
    phone_number_display = forms.CharField(
        required=False,
        label="Numéro de téléphone",
        widget=forms.TextInput(attrs={
            'class': 'phone-number form-control',
            'id': 'id_phone_number_display',
        })
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'other_first_name', 'email', 'birth_date',
            'nationality', 'birth_country', 'blood_group', 'address',
            'id_type', 'id_number', 'professional_email', 'allergies',
            'recurring_illness', 'special_allergies', 'isignum_number', 'eritop_id',
            'bank', 'bank_account_number', 'social_security_number', 'profile_picture'
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom'
            }),
            'other_first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Autre prénom (optionnel)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@personnel.com'
            }),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'id_type': forms.Select(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de votre pièce d\'identité'
            }),
            'professional_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'prenom.nom@entreprise.com'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Allergies connues (optionnel)'
            }),
            'recurring_illness': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Maladies récurrentes (optionnel)'
            }),
            'special_allergies': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Allergies spécifiques (optionnel)'
            }),
            'isignum_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro Isignum (optionnel)'
            }),
            'eritop_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ID Eritop (optionnel)'
            }),
            'bank': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre banque'
            }),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de compte bancaire'
            }),
            'social_security_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de sécurité sociale'
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.phone_number:
            self.fields['phone_number_display'].initial = str(self.instance.phone_number)
        
        # Personnalisation des labels
        self.fields['professional_email'].label = "Adresse email professionnelle"
        self.fields['id_number'].label = "Numéro de la pièce d'identité"
        self.fields['bank_account_number'].label = "Numéro de compte bancaire"
        self.fields['social_security_number'].label = "Numéro de sécurité sociale"
        
        # Ajout de tooltips pour l'utilisateur
        self.fields['professional_email'].help_text = "Votre email professionnel officiel"
        self.fields['id_number'].help_text = "Doit correspondre à votre pièce d'identité"

    def clean(self):
        cleaned_data = super().clean()
        raw_number = cleaned_data.get('phone_number_display')

        # Si le champ est vide, on s'assure que le numéro de modèle est aussi vide.
        if not raw_number:
            cleaned_data['phone_number'] = None
            return cleaned_data

        raw_number = raw_number.strip()
        
        # Le front-end (intl-tel-input) est censé TOUJOURS envoyer un numéro avec '+'
        if not raw_number.startswith('+'):
            try:
                # On suppose que c'est un numéro local (Bénin)
                parsed_number = phonenumbers.parse(raw_number, "BJ")
            except phonenumbers.NumberParseException:
                self.add_error('phone_number_display', "Format du numéro de téléphone invalide.")
                return cleaned_data
        else:
            try:
                # Le numéro a déjà un indicatif
                parsed_number = phonenumbers.parse(raw_number, None)
            except phonenumbers.NumberParseException:
                self.add_error('phone_number_display', "Format du numéro de téléphone invalide.")
                return cleaned_data

        # Validation basique
        if not phonenumbers.is_possible_number(parsed_number):
            self.add_error('phone_number_display', "Le numéro de téléphone ne semble pas correct (vérifiez la longueur).")
        else:
            # Stockage au format E.164
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
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.txt'
            })
        }
        labels = {
            'document_type': "Type de document",
            'document': "Fichier"
        }
        help_texts = {
            'document': "Téléchargez le document (max 10MB). Formats: PDF, Word, JPG, PNG, TXT."
        }

    def clean_document(self):
        document = self.cleaned_data.get('document')
        if document:
            # Vérification de la taille
            if document.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Le fichier est trop volumineux. Taille maximale: 10MB.")

            # Vérification de l'extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt']
            file_ext = '.' + document.name.split('.')[-1].lower() if '.' in document.name else ''
            
            if file_ext not in allowed_extensions:
                raise forms.ValidationError(
                    "Type de fichier non supporté. Formats autorisés: PDF, Word, JPG, PNG, TXT."
                )
            
            # Vérification du type MIME (optionnel mais plus sécurisé)
            allowed_mime_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'image/jpeg',
                'image/png',
                'text/plain'
            ]
            
            if hasattr(document, 'content_type') and document.content_type not in allowed_mime_types:
                raise forms.ValidationError("Type de fichier non autorisé.")
                
        return document