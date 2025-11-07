from django.db import models
from django.conf import settings

class PermissionRequest(models.Model):
    REQUEST_TYPES = (
        ('permission', 'Permission'),
        ('leave', 'Congé'),
        ('certification', 'Demande de certification'),
        ('attestation', 'Demande d\'attestation'),
    )

    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='permission_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_request_type_display()} for {self.user.username} from {self.start_date} to {self.end_date}"

class ApprovalStep(models.Model):
    request = models.ForeignKey(PermissionRequest, on_delete=models.CASCADE, related_name='approval_steps')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approval_steps')
    approved_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"Approval for {self.request} by {self.approver.username}"