from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.db.models import ForeignKey, DateField, OneToOneField
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import login

from datetime import date, datetime
import json
import os
import io
from PIL import Image

from .forms import EnhancedLoginForm, EmployeeCreateForm, ProfileUpdateForm, EmployeeDocumentForm
from .models import CustomUser, ProfileUpdate, EmployeeDocument
from phonenumber_field.phonenumber import PhoneNumber


class EnhancedLoginView(View):
    """Vue améliorée pour la connexion"""
    template_name = 'registration/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:home')  # Redirige vers la page d'accueil si déjà connecté
        
        form = EnhancedLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = EnhancedLoginForm(request, data=request.POST)
        if form.is_valid():
            from django.contrib.auth import login
            
            user = form.get_user()
            login(request, user)
            
            # Gestion de "Se souvenir de moi"
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Session expire à la fermeture du navigateur
            else:
                request.session.set_expiry(1209600)  # 2 semaines
            
            # Redirection après connexion
            next_url = request.POST.get('next') or 'core:home'
            return redirect(next_url)
        
        # Si le formulaire est invalide
        messages.error(request, "Identifiants incorrects. Veuillez réessayer.")
        return render(request, self.template_name, {'form': form})


class EmployeeListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20
    
    def get_queryset(self):
        # Filtrer seulement les employés actifs
        return CustomUser.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_employees'] = self.get_queryset().count()
        return context


class EmployeeCreateView(LoginRequiredMixin, View):
    """Création d'un nouvel employé"""
    def get(self, request):
        form = EmployeeCreateForm()
        return render(request, 'users/employee_create.html', {'form': form})

    def post(self, request):
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                
                messages.success(request, 
                    f"L'employé {user.get_full_name()} a été créé avec succès."
                )
                return redirect('users:employee_list')
                
            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        return render(request, 'users/employee_create.html', {'form': form})


class ProfileUpdateView(LoginRequiredMixin, View):
    """Mise à jour du profil utilisateur"""
    
    def get(self, request):
        # Vérifier si une demande est en attente
        pending_update = ProfileUpdate.objects.filter(
            employee=request.user,
            status='pending'
        ).first()
        
        if pending_update:
            messages.info(request, "Vous avez une demande de mise à jour en attente.")
            return redirect('users:profile_update_pending')
        
        # Initialiser le formulaire avec les données actuelles
        form = ProfileUpdateForm(instance=request.user)
        
        # Récupérer les documents
        documents = request.user.documents.all()
        
        # Récupérer la dernière demande traitée
        last_processed = ProfileUpdate.objects.filter(
            employee=request.user
        ).exclude(status='pending').order_by('-created_at').first()
        
        context = {
            'form': form,
            'documents': documents,
            'last_processed': last_processed,
        }
        
        return render(request, 'users/profile_update.html', context)

    def post(self, request):
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    data = form.cleaned_data
                    serializable_data = {}
                    changed_fields = list(form.changed_data)
                    
                    # Gestion de la photo de profil
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
                    
                    # Traitement des autres champs
                    for field_name in changed_fields:
                        value = data.get(field_name)
                        
                        if field_name == 'phone_number_display':
                            serializable_data['phone_number'] = data.get('phone_number')
                            continue
                        
                        try:
                            field = CustomUser._meta.get_field(field_name)
                        except FieldDoesNotExist:
                            continue
                        
                        # Gestion des valeurs vides
                        if value is None or value == '':
                            serializable_data[field_name] = None
                        
                        # Gestion des ForeignKey et OneToOneField
                        elif isinstance(field, (ForeignKey, OneToOneField)):
                            if value:  # value est l'objet complet
                                serializable_data[field_name] = value.pk
                            else:
                                serializable_data[field_name] = None
                        
                        # Gestion des dates
                        elif isinstance(field, DateField) and isinstance(value, (date, datetime)):
                            serializable_data[field_name] = value.isoformat()
                        
                        # Gestion des PhoneNumber
                        elif isinstance(value, PhoneNumber):
                            serializable_data[field_name] = str(value)
                        
                        # Valeurs simples
                        else:
                            serializable_data[field_name] = value
                    
                    # Vérifier s'il y a des changements
                    if not serializable_data:
                        messages.info(request, "Aucun changement détecté.")
                        return redirect('users:profile_update')
                    
                    # Créer ou mettre à jour la demande
                    ProfileUpdate.objects.update_or_create(
                        employee=request.user,
                        status='pending',
                        defaults={
                            'data': serializable_data,
                            'comments': '',
                            'reviewed_by': None,
                            'reviewed_at': None
                        }
                    )
                
                messages.success(request, 
                    "Votre demande de mise à jour a été soumise avec succès. "
                    "Elle est en attente de validation."
                )
                return redirect('users:profile_update_pending')
                
            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        # En cas d'erreur, re-afficher le formulaire
        documents = request.user.documents.all()
        return render(request, 'users/profile_update.html', {
            'form': form,
            'documents': documents
        })


class ProfileUpdatePendingView(LoginRequiredMixin, View):
    """Vue pour les demandes de mise à jour en attente"""
    
    def get(self, request):
        pending_update = ProfileUpdate.objects.filter(
            employee=request.user,
            status='pending'
        ).first()
        
        if not pending_update:
            messages.info(request, "Aucune demande en attente.")
            return redirect('users:profile_update')
        
        return render(request, 'users/profile_update_pending.html', {
            'pending_update': pending_update
        })


class ProfileUpdateListView(LoginRequiredMixin, ListView):
    """Liste des demandes de mise à jour à approuver (pour les managers)"""
    model = ProfileUpdate
    template_name = 'users/profile_update_list.html'
    context_object_name = 'updates'
    paginate_by = 10
    
    def get_queryset(self):
        # Seulement les demandes en attente
        return ProfileUpdate.objects.filter(status='pending').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = self.get_queryset().count()
        return context


class ProfileUpdateDetailView(LoginRequiredMixin, View):
    """Détail d'une demande de mise à jour"""
    
    def get(self, request, pk):
        update = get_object_or_404(ProfileUpdate, pk=pk)
        
        # Formater les données pour l'affichage
        formatted_data = {}
        for field_name, new_value in update.data.items():
            # Récupérer le nom du champ formaté
            field_label = field_name.replace('_', ' ').title()
            
            # Récupérer l'ancienne valeur
            try:
                old_value = getattr(update.employee, field_name)
                
                # Pour les ForeignKey, obtenir l'objet
                try:
                    field = update.employee._meta.get_field(field_name)
                    if isinstance(field, (ForeignKey, OneToOneField)):
                        if old_value:
                            old_value = str(old_value)
                        if new_value:
                            try:
                                related_obj = field.related_model.objects.get(pk=new_value)
                                new_value = str(related_obj)
                            except field.related_model.DoesNotExist:
                                new_value = f"[Objet introuvable: ID {new_value}]"
                except FieldDoesNotExist:
                    pass
                    
            except AttributeError:
                old_value = "Non défini"
            
            # Formatage des valeurs None
            if old_value is None:
                old_value = "Non défini"
            if new_value is None:
                new_value = "Non défini"
            
            formatted_data[field_label] = {
                'old': old_value,
                'new': new_value
            }
        
        context = {
            'update': update,
            'formatted_data': formatted_data
        }
        return render(request, 'users/profile_update_detail.html', context)

    def post(self, request, pk):
        update = get_object_or_404(ProfileUpdate, pk=pk, status='pending')
        employee = update.employee
        action = request.POST.get('action')
        comments = request.POST.get('comments', '').strip()
        
        try:
            with transaction.atomic():
                if action == 'approve':
                    # Appliquer les changements
                    for field_name, value in update.data.items():
                        if field_name == 'profile_picture':
                            self._handle_profile_picture(employee, value)
                        else:
                            self._apply_field_update(employee, field_name, value)
                    
                    employee.save()
                    
                    # Mettre à jour la demande
                    update.status = 'approved'
                    update.comments = comments
                    update.reviewed_by = request.user
                    update.reviewed_at = timezone.now()
                    update.save()
                    
                    messages.success(request, 
                        f"La mise à jour du profil de {employee.get_full_name()} a été approuvée."
                    )
                    
                elif action == 'reject':
                    update.status = 'rejected'
                    update.comments = comments
                    update.reviewed_by = request.user
                    update.reviewed_at = timezone.now()
                    update.save()
                    
                    messages.warning(request, "La demande a été rejetée.")
                
                else:
                    messages.error(request, "Action non reconnue.")
                    
        except Exception as e:
            messages.error(request, f"Erreur lors du traitement : {str(e)}")
        
        return redirect('users:profile_update_list')
    
    def _handle_profile_picture(self, employee, filename):
        """Gère la photo de profil"""
        if filename is None:
            # Supprimer la photo
            if employee.profile_picture:
                employee.profile_picture.delete(save=False)
            employee.profile_picture = None
            return
        
        # Traiter la nouvelle photo
        temp_path = os.path.join(settings.TEMP_MEDIA_ROOT, filename)
        if os.path.exists(temp_path):
            try:
                # Redimensionner l'image
                img = Image.open(temp_path)
                img.thumbnail((300, 300))
                
                # Sauvegarder
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG', quality=85)
                img_content = ContentFile(img_io.getvalue())
                
                # Générer un nom unique
                from django.utils.text import get_valid_filename
                unique_name = f"profile_{employee.pk}_{int(timezone.now().timestamp())}.jpg"
                
                employee.profile_picture.save(unique_name, img_content, save=False)
                
                # Nettoyer le fichier temporaire
                os.remove(temp_path)
                
            except Exception as e:
                raise Exception(f"Erreur de traitement d'image : {str(e)}")
        else:
            raise Exception("Fichier temporaire introuvable")
    
    def _apply_field_update(self, employee, field_name, value):
        """Applique une mise à jour de champ"""
        try:
            field = employee._meta.get_field(field_name)
        except FieldDoesNotExist:
            return
        
        # Gestion des ForeignKey
        if isinstance(field, (ForeignKey, OneToOneField)):
            if value is None:
                setattr(employee, field_name, None)
            else:
                try:
                    related_obj = field.related_model.objects.get(pk=value)
                    setattr(employee, field_name, related_obj)
                except field.related_model.DoesNotExist:
                    raise Exception(f"Objet lié introuvable pour {field_name} (ID: {value})")
        
        # Gestion des dates
        elif isinstance(field, DateField) and isinstance(value, str):
            try:
                date_obj = datetime.fromisoformat(value).date()
                setattr(employee, field_name, date_obj)
            except ValueError:
                raise Exception(f"Format de date invalide pour {field_name}")
        
        # Champs simples
        else:
            setattr(employee, field_name, value)


class EmployeeDocumentUploadView(LoginRequiredMixin, View):
    """Upload de documents pour l'employé"""
    
    def get(self, request):
        form = EmployeeDocumentForm()
        documents = request.user.documents.all()
        return render(request, 'users/employee_document_upload.html', {
            'form': form,
            'documents': documents
        })

    def post(self, request):
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.employee = request.user
                document.save()
                
                messages.success(request, "Document téléchargé avec succès.")
                return redirect('users:profile_update')
                
            except Exception as e:
                messages.error(request, f"Erreur lors du téléchargement : {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        documents = request.user.documents.all()
        return render(request, 'users/employee_document_upload.html', {
            'form': form,
            'documents': documents
        })