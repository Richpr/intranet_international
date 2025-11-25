from django.urls import path
from .views import (
    EmployeeListView,
    EmployeeCreateView, 
    ProfileUpdateView, 
    ProfileUpdatePendingView, 
    ProfileUpdateListView, 
    ProfileUpdateDetailView,
    EmployeeDocumentUploadView
)

app_name = 'users'

urlpatterns = [
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employee/add/', EmployeeCreateView.as_view(), name='employee_add'),
    path('profile/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/pending/', ProfileUpdatePendingView.as_view(), name='profile_update_pending'),
    path('profile/updates/', ProfileUpdateListView.as_view(), name='profile_update_list'),
    path('profile/updates/<int:pk>/', ProfileUpdateDetailView.as_view(), name='profile_update_detail'),
    path('documents/upload/', EmployeeDocumentUploadView.as_view(), name='employee_document_upload'),
]
