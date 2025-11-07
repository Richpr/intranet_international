from django.views.generic import ListView, CreateView
from .models import Document, DocumentType
from .forms import DocumentForm
from django.urls import reverse_lazy

class DocumentListView(ListView):
    model = Document
    template_name = 'documentation/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        queryset = super().get_queryset()
        doc_type = self.request.GET.get('type')
        if doc_type:
            queryset = queryset.filter(document_type__name=doc_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_types'] = DocumentType.objects.all()
        return context

class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'documentation/document_form.html'
    success_url = reverse_lazy('documentation:document_list')