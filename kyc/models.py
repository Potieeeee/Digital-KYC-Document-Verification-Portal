from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class KYCProfile(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("resubmission_required", "Resubmission Required"),
    ]

    RISK_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="kyc_profile")
    reference_code = models.CharField(max_length=30, unique=True, blank=True)

    full_name = models.CharField(max_length=150)
    birth_date = models.DateField()
    address = models.TextField()
    phone_number = models.CharField(max_length=20)

    id_type = models.CharField(max_length=50)
    id_number_hash = models.CharField(max_length=255, blank=True)
    id_number_masked = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")
    risk_score = models.IntegerField(default=0)
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default="low")
    risk_flags = models.JSONField(default=list, blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def submit(self):
        self.status = "submitted"
        self.submitted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.full_name} - {self.status}"


class KYCDocument(models.Model):
    DOCUMENT_TYPES = [
        ("front_id", "Front ID"),
        ("back_id", "Back ID"),
        ("selfie", "Selfie Verification Photo"),
        ("supporting", "Supporting Document"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("valid", "Valid"),
        ("invalid", "Invalid"),
        ("needs_resubmission", "Needs Resubmission"),
    ]

    profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to="kyc_documents/")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    remarks = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.full_name} - {self.document_type}"


class KYCReview(models.Model):
    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("resubmission_required", "Resubmission Required"),
    ]

    profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    decision = models.CharField(max_length=30, choices=DECISION_CHOICES)
    remarks = models.TextField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.full_name} - {self.decision}"
# Create your models here.
