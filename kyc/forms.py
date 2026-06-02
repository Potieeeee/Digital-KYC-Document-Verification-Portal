import hashlib
from django import forms
from django.forms import inlineformset_factory
from .models import KYCProfile, KYCDocument, KYCReview

class KYCProfileForm(forms.ModelForm):
    id_number = forms.CharField(max_length=50, required=True)

    class Meta:
        model = KYCProfile
        fields = [
            "full_name",
            "birth_date",
            "address",
            "phone_number",
            "id_type",
            "id_number",
        ]

        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, commit=True):
        profile = super().save(commit=False)
        raw_id_number = self.cleaned_data["id_number"]

        profile.id_number_hash = hashlib.sha256(raw_id_number.encode()).hexdigest()
        profile.id_number_masked = "****" + raw_id_number[-4:]

        if commit:
            profile.save()

        return profile


class KYCDocumentForm(forms.ModelForm):
    class Meta:
        model = KYCDocument
        fields = ["document_type", "file"]


KYCDocumentFormSet = inlineformset_factory(
    KYCProfile,
    KYCDocument,
    form=KYCDocumentForm,
    can_delete=True,
    max_num=3,
    validate_max=True,
)


class KYCReviewForm(forms.ModelForm):
    class Meta:
        model = KYCReview
        fields = ["decision", "remarks"]