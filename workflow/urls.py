from django.urls import path
from .views import (
    PermissionRequestCreateView, 
    PermissionRequestListView,
    PermissionRequestDetailView,
    PermissionRequestPdfView,
    ApprovalRequestListView,
    ApprovalRequestUpdateView
)

app_name = 'workflow'

urlpatterns = [
    path('requests/', PermissionRequestListView.as_view(), name='request_list'),
    path('requests/new/', PermissionRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', PermissionRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/pdf/', PermissionRequestPdfView.as_view(), name='request_pdf'),
    path('approvals/', ApprovalRequestListView.as_view(), name='approval_list'),
    path('approvals/<int:pk>/', ApprovalRequestUpdateView.as_view(), name='approval_update'),
]
