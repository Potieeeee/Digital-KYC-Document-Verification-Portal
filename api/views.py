from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from kyc.models import KYCProfile
from .serializers import KYCProfileSerializer, ThirdPartyKYCStatusSerializer
from .permissions import IsReviewerManagerAdmin, IsThirdPartyAPI
from auditlog.services import create_audit_log
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

@method_decorator(
    ratelimit(key="user", rate="10/m", method="GET", block=True),
    name="dispatch"
)
class MyKYCAPIView(APIView):
    def get(self, request):
        profile = KYCProfile.objects.filter(user=request.user).first()

        if not profile:
            return Response({"detail": "No KYC profile found."}, status=404)

        serializer = KYCProfileSerializer(profile, context={"request": request})

        create_audit_log(
            actor=request.user,
            action="API_VIEW_OWN_KYC",
            object_type="KYCProfile",
            object_id=profile.id,
            request=request
        )

        return Response(serializer.data)


class AdminKYCListAPIView(APIView):
    # permission_classes = [IsReviewerManagerAdmin]

    def get(self, request):
        profiles = KYCProfile.objects.all().order_by("-created_at")
        serializer = KYCProfileSerializer(profiles, many=True, context={"request": request})

        create_audit_log(
            actor=request.user,
            action="API_ADMIN_KYC_LIST",
            object_type="KYCProfile",
            object_id="list",
            request=request
        )

        return Response(serializer.data)


class ThirdPartyKYCStatusAPIView(APIView):
    permission_classes = [IsThirdPartyAPI]

    def get(self, request, reference_code):
        profile = KYCProfile.objects.filter(reference_code=reference_code).first()

        if not profile:
            return Response({"detail": "KYC reference not found."}, status=404)

        serializer = ThirdPartyKYCStatusSerializer(profile)

        create_audit_log(
            actor=request.user,
            action="THIRD_PARTY_STATUS_FETCH",
            object_type="KYCProfile",
            object_id=profile.id,
            metadata={"reference_code": reference_code},
            request=request
        )

        return Response(serializer.data)


class BackgroundCheckWebhookAPIView(APIView):
    permission_classes = [IsThirdPartyAPI]

    def post(self, request):
        reference_code = request.data.get("reference_code")
        result = request.data.get("result")
        remarks = request.data.get("remarks")

        profile = KYCProfile.objects.filter(reference_code=reference_code).first()

        if not profile:
            return Response({"detail": "KYC reference not found."}, status=404)

        create_audit_log(
            actor=request.user,
            action="BACKGROUND_CHECK_RESULT_RECEIVED",
            object_type="KYCProfile",
            object_id=profile.id,
            metadata={
                "result": result,
                "remarks": remarks,
            },
            request=request
        )

        return Response({
            "message": "Background check result received.",
            "reference_code": reference_code,
            "result": result,
        }, status=status.HTTP_200_OK)