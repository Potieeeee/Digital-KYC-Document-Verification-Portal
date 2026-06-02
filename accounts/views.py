from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import RegisterForm, LoginForm
from auditlog.services import create_audit_log

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            client_group = Group.objects.get(name="Client")
            user.groups.add(client_group)

            create_audit_log(
                actor=user,
                action="USER_REGISTERED",
                object_type="User",
                object_id=user.id,
                metadata={"email": user.email},
                request=request
            )

            messages.success(request, "Account created successfully. You may now log in")
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})

from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from kyc.models import KYCProfile


@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True),
    name="dispatch"
)
@method_decorator(
    ratelimit(key="post:username", rate="5/m", method="POST", block=True),
    name="dispatch"
)
class RateLimitedLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm

    def get_success_url(self):
        redirect_to = self.get_redirect_url()

        if redirect_to:
            return redirect_to

        user = self.request.user
        if user.groups.filter(name__in=["Reviewer", "Manager", "Admin"]).exists():
            return reverse_lazy("reviewer_dashboard")
        
        if user.groups.filter(name="Client").exists():
            return "/dashboard/"

        if user.groups.filter(name="ThirdPartyAPI").exists():
            return "/"

        return "/dashboard/"


@login_required
def profile_view(request):
    """Redirect authenticated users to their KYC profile detail or KYC creation."""
    try:
        profile = request.user.kyc_profile
        return redirect('client_kyc_detail', profile_id=profile.id)
    except KYCProfile.DoesNotExist:
        return redirect('create_kyc')