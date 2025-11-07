from django.urls import path
from .views import DocumentListView, DocumentCreateView

app_name = 'documentation'

urlpatterns = [
    path('', DocumentListView.as_view(), name='document_list'),
    path('new/', DocumentCreateView.as_view(), name='document_create'),
]
