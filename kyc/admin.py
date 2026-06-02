from django.contrib import admin
from .models import KYCProfile, KYCDocument, KYCReview

admin.site.register(KYCProfile)
admin.site.register(KYCDocument)
admin.site.register(KYCReview)