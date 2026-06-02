from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

INPUT_CLASS = "w-full border rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary"


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}))

    website = forms.CharField(required=False)  # honeypot field

    class Meta:
        model = User
        fields = ["username", "email", "password"]
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'password': forms.PasswordInput(attrs={'class': INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ensure confirm_password exists on form even if not in model fields
        if 'confirm_password' not in self.fields:
            self.fields['confirm_password'] = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}), required=True)

        # Add classes to any other fields added later
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = INPUT_CLASS

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        website = cleaned_data.get("website")

        if website:
            raise forms.ValidationError("Spam registration blocked.")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': INPUT_CLASS}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}))