from rest_framework import serializers
from kyc.models import KYCProfile, KYCDocument

class KYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = ["id", "document_type", "status", "uploaded_at"]


class KYCProfileSerializer(serializers.ModelSerializer):
    documents = KYCDocumentSerializer(many=True, read_only=True)
    id_number = serializers.SerializerMethodField()

    class Meta:
        model = KYCProfile
        fields = [
            "id",
            "reference_code",
            "full_name",
            "status",
            "risk_level",
            "risk_score",
            "id_number",
            "documents",
        ]

    def get_id_number(self, obj):
        request = self.context.get("request")

        if request and request.user.groups.filter(name__in=["Reviewer", "Manager", "Admin"]).exists():
            return obj.id_number_masked

        return "Hidden"


class ThirdPartyKYCStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = [
            "reference_code",
            "status",
            "risk_level",
            "updated_at",
        ]