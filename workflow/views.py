from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import PermissionRequest, ApprovalStep
from .forms import PermissionRequestForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.utils import timezone

class PermissionRequestCreateView(LoginRequiredMixin, CreateView):
    model = PermissionRequest
    form_class = PermissionRequestForm
    template_name = 'workflow/permissionrequest_form.html'
    success_url = reverse_lazy('workflow:request_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class PermissionRequestListView(LoginRequiredMixin, ListView):
    model = PermissionRequest
    template_name = 'workflow/permissionrequest_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return PermissionRequest.objects.filter(user=self.request.user).order_by('-created_at')

class PermissionRequestDetailView(LoginRequiredMixin, DetailView):
    model = PermissionRequest
    template_name = 'workflow/permissionrequest_detail.html'
    context_object_name = 'request'

class PermissionRequestPdfView(LoginRequiredMixin, DetailView):
    model = PermissionRequest

    def get_template_names(self):
        if self.object.request_type == 'certification':
            return ['workflow/certification_pdf.html']
        elif self.object.request_type == 'attestation':
            return ['workflow/attestation_pdf.html']
        return ['workflow/permission_pdf.html']

    def render_to_response(self, context, **response_kwargs):
        html_string = render_to_string(self.get_template_names(), context)
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{self.object.request_type}_{self.object.pk}.pdf"'
        return response

class ApprovalRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = PermissionRequest
    template_name = 'workflow/approvalrequest_list.html'
    context_object_name = 'requests'

    def test_func(self):
        return self.request.user.is_cm

    def get_queryset(self):
        return PermissionRequest.objects.filter(status='pending').order_by('created_at')

class ApprovalRequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PermissionRequest
    fields = ['status']
    template_name = 'workflow/approvalrequest_form.html'
    success_url = reverse_lazy('workflow:approval_list')

    def test_func(self):
        return self.request.user.is_cm

    def form_valid(self, form):
        request = self.get_object()
        approval, created = ApprovalStep.objects.get_or_create(request=request, approver=self.request.user)
        if form.instance.status == 'approved':
            approval.approved_at = timezone.now()
            approval.save()
        return super().form_valid(form)