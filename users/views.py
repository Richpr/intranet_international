from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import EmployeeCreateForm, ProfileUpdateForm, EmployeeDocumentForm
from .models import CustomUser, ProfileUpdate
import json
from django.db.models import ForeignKey, DateField  # IMPORT AJOUTÉ
from datetime import date, datetime
from PIL import Image
from django.core.files.base import ContentFile
import io
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from django.contrib import messages
from django.views.generic import ListView
from phonenumber_field.phonenumber import PhoneNumber

class EmployeeListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/employee_list.html'
    context_object_name = 'employees'

class EmployeeCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = EmployeeCreateForm()
        return render(request, 'users/employee_create.html', {'form': form})

    def post(self, request):
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:employee_list') # Assumes you have a user list view
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous pour créer l'employé.")
        return render(request, 'users/employee_create.html', {'form': form})

class ProfileUpdateView(LoginRequiredMixin, View):
    def get(self, request):
        form = ProfileUpdateForm(instance=request.user)
        
        # Récupérer la dernière demande de mise à jour, quel que soit son statut
        last_update = ProfileUpdate.objects.filter(employee=request.user).last()

        # Si une demande est en attente, on redirige vers la page dédiée
        if last_update and last_update.status == 'pending':
            messages.info(request, "Vous avez une demande de mise à jour de profil en attente d'approbation.")
            return redirect('users:profile_update_pending')

        # Get user's documents
        documents = request.user.documents.all()

        context = {
            'form': form,
            'last_update': last_update,
            'documents': documents
        }
            
        return render(request, 'users/profile_update.html', context)

    def post(self, request):
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            data = form.cleaned_data
            serializable_data = {}
            # Use a copy of changed_data as we might modify it
            changed_fields = list(form.changed_data)

            # --- Gestion de la photo de profil ---
            if 'profile_picture' in request.FILES:
                file = request.FILES['profile_picture']
                fs = FileSystemStorage(location=settings.TEMP_MEDIA_ROOT)
                temp_filename = fs.save(file.name, file)
                serializable_data['profile_picture'] = temp_filename
                if 'profile_picture' in changed_fields:
                    changed_fields.remove('profile_picture')
            elif 'profile_picture' in changed_fields and not data.get('profile_picture'):
                serializable_data['profile_picture'] = None
                if 'profile_picture' in changed_fields:
                    changed_fields.remove('profile_picture')

            # --- Traitement des autres champs modifiés ---
            for key in changed_fields:
                value = data.get(key)

                if key == 'phone_number_display':
                    # 'phone_number' est le champ du modèle, rempli par la méthode clean du formulaire
                    serializable_data['phone_number'] = data.get('phone_number')
                    continue

                try:
                    field = CustomUser._meta.get_field(key);
                except FieldDoesNotExist:
                    # Ce champ n'est pas un champ de modèle, on l'ignore pour la sérialisation
                    continue

                if value is None or value == '':
                    serializable_data[key] = None
                elif isinstance(field, ForeignKey) or field.one_to_one:
                    serializable_data[key] = value.pk
                elif isinstance(value, (date, datetime)):
                    serializable_data[key] = value.isoformat()
                elif isinstance(value, PhoneNumber):
                    serializable_data[key] = str(value)
                else:
                    serializable_data[key] = value
            
            if not serializable_data:
                messages.info(request, "Aucun changement détecté dans votre profil.")
                return redirect('users:profile_update')

            # --- Utilisation de update_or_create pour éviter l'IntegrityError ---
            ProfileUpdate.objects.update_or_create(
                employee=request.user,
                defaults={
                    'data': serializable_data,
                    'status': 'pending',
                    'comments': '',
                    'reviewed_by': None,
                    'reviewed_at': None
                }
            )
            messages.success(request, "Votre demande de mise à jour de profil a été soumise avec succès et est en attente de validation.")
            return redirect('users:profile_update_pending')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        return render(request, 'users/profile_update.html', {'form': form})

class ProfileUpdatePendingView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'users/profile_update_pending.html')

class ProfileUpdateListView(LoginRequiredMixin, View):
    def get(self, request):
        updates = ProfileUpdate.objects.filter(status='pending')
        return render(request, 'users/profile_update_list.html', {'updates': updates})

class ProfileUpdateDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        update = ProfileUpdate.objects.get(pk=pk)
        
        formatted_data = {}
        for key, new_value in update.data.items():
            field_name = key.replace('_', ' ').capitalize()
            
            old_value = getattr(update.employee, key, '')
            
            # If the field is a foreign key, get the display value
            field = update.employee._meta.get_field(key)
            if field.is_relation:
                try:
                    # Get the related object for the old value
                    if old_value:
                        old_value = field.related_model.objects.get(pk=old_value.pk)
                    
                    # Get the related object for the new value
                    new_value = field.related_model.objects.get(pk=new_value)
                except field.related_model.DoesNotExist:
                    new_value = f"ID {new_value} (introuvable)"
            
            formatted_data[field_name] = {'old': old_value, 'new': new_value}

        context = {
            'update': update,
            'formatted_data': formatted_data
        }
        return render(request, 'users/profile_update_detail.html', context)

    def post(self, request, pk):
        try:
            update = ProfileUpdate.objects.get(pk=pk, status='pending')
        except ProfileUpdate.DoesNotExist:
            messages.error(request, 'Demande de mise à jour introuvable ou déjà traitée.')
            return redirect('users:profile_update_list')

        employee = update.employee
        data_to_update = update.data

        if 'approve' in request.POST:
            # Traitement des données avant l'application
            for key, value in data_to_update.items():
                field = employee._meta.get_field(key)
                
                # Désérialisation pour les clés étrangères
                if isinstance(field, ForeignKey) or field.one_to_one:
                    # 'value' est l'ID (int). Récupérer l'objet.
                    try:
                        # Obtenir le modèle lié.
                        model = field.related_model
                        obj = model.objects.get(pk=value)
                        setattr(employee, key, obj)
                    except model.DoesNotExist:
                         messages.warning(request, f"L'objet lié pour le champ '{key}' (ID: {value}) n'existe plus. Champ ignoré.")
                         continue
                
                # Désérialisation pour les dates
                elif isinstance(field, DateField) and isinstance(value, str):
                    try:
                        date_obj = datetime.fromisoformat(value).date()
                        setattr(employee, key, date_obj)
                    except ValueError:
                         messages.warning(request, f"Format de date invalide pour le champ '{key}'. Champ ignoré.")
                         continue
                
                # Gestion de la photo de profil (FileField)
                elif key == 'profile_picture' and value is not None:
                    # Le 'value' est le nom du fichier temporaire
                    fs = FileSystemStorage(location=settings.TEMP_MEDIA_ROOT)
                    temp_path = os.path.join(settings.TEMP_MEDIA_ROOT, value)

                    if os.path.exists(temp_path):
                        # Lecture du fichier temporaire et redimensionnement (si nécessaire, comme dans votre code initial)
                        try:
                            img = Image.open(temp_path)
                            img.thumbnail((300, 300))
                            img_io = io.BytesIO()
                            img.save(img_io, format='JPEG')
                            # Sauvegarde sur le champ du modèle
                            employee.profile_picture.save(value, ContentFile(img_io.getvalue()), save=False)
                            os.remove(temp_path) # Nettoyage du fichier temp
                        except Exception as e:
                            messages.error(request, f"Erreur lors du traitement de l'image : {e}")
                            continue
                    else:
                        messages.warning(request, "Fichier temporaire de la photo de profil introuvable.")
                
                # Rétablir la suppression de la photo si value est None
                elif key == 'profile_picture' and value is None:
                    employee.profile_picture = None
                
                # Cas par défaut pour les champs simples
                else:
                    setattr(employee, key, value)
                    
            employee.save()
            update.status = 'approved'
            update.reviewed_by = request.user
            update.reviewed_at = datetime.now()
            update.comments = request.POST.get('comments', '')
            update.save()
            messages.success(request, 'La mise à jour du profil a été approuvée.')
        
        elif 'reject' in request.POST:
            # ... (Logique de rejet inchangée)
            update.status = 'rejected'
            update.comments = request.POST.get('comments', '')
            update.reviewed_by = request.user
            update.reviewed_at = datetime.now()
            update.save()
            messages.error(request, 'La mise à jour du profil a été rejetée.')
            
        return redirect('users:profile_update_list')

class EmployeeDocumentUploadView(LoginRequiredMixin, View):
    def get(self, request):
        form = EmployeeDocumentForm()
        return render(request, 'users/employee_document_upload.html', {'form': form})

    def post(self, request):
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = request.user
            document.save()
            return redirect('users:profile_update')
        return render(request, 'users/employee_document_upload.html', {'form': form})