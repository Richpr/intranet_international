from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    EmployeeListView,
    EmployeeUpdateView,
    EmployeeCreateView, 
    ProfileUpdateView, 
    ProfileUpdatePendingView, 
    ProfileUpdateListView, 
    ProfileUpdateDetailView,
    EmployeeDocumentUploadView,
    EnhancedLoginView,
    ProfileUpdateHistoryView,
    EmployeeDetailView
)

app_name = 'users'

urlpatterns = [
    # URLs d'authentification
    path('login/', EnhancedLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/users/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/users/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # URLs des employés
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employee/add/', EmployeeCreateView.as_view(), name='employee_add'),
    path('employee/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),

    # 💡 AJOUTEZ CETTE LIGNE MANQUANTE
    path('employee/<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    
    # URLs de profil
    path('profile/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/pending/', ProfileUpdatePendingView.as_view(), name='profile_update_pending'),
    path('profile/history/', ProfileUpdateHistoryView.as_view(), name='profile_update_history'),
    path('profile/updates/', ProfileUpdateListView.as_view(), name='profile_update_list'),
    path('profile/updates/<int:pk>/', ProfileUpdateDetailView.as_view(), name='profile_update_detail'),
    
    # URLs de documents
    path('documents/upload/', EmployeeDocumentUploadView.as_view(), name='employee_document_upload'),
    
    # URL de changement de mot de passe
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url='/users/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),
]