from datetime import date

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from config.tailwind_forms import TailwindFormMixin

from .models import User


def _age(birth_date):
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


class RegisterForm(TailwindFormMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")
    terms_accepted = forms.BooleanField(
        required=True, label="Aceito os termos de uso"
    )

    class Meta:
        model = User
        fields = [
            "email",
            "nickname",
            "name",
            "birth_date",
            "sex",
            "height",
            "password",
            "password_confirm",
            "terms_accepted",
        ]
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"})}

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este email já está em uso.")
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data["nickname"].strip()
        if len(nickname) < 3:
            raise ValidationError("O nickname deve ter no mínimo 3 caracteres.")
        if User.objects.filter(nickname=nickname).exists():
            raise ValidationError("Este nickname já está em uso.")
        return nickname

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        age = _age(birth_date)
        if age < 10 or age > 120:
            raise ValidationError("Idade deve estar entre 10 e 120 anos.")
        return birth_date

    def clean_height(self):
        height = self.cleaned_data["height"]
        if height < 50 or height > 300:
            raise ValidationError("Altura deve estar entre 50 e 300 cm.")
        return height

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "As senhas não coincidem.")
        if password:
            password_validation.validate_password(password)
        return cleaned_data


class LoginForm(TailwindFormMixin, forms.Form):
    login = forms.CharField(label="Email ou nickname")
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")


class ProfileForm(TailwindFormMixin, forms.ModelForm):
    """Só name e height são editáveis, conforme USERS_MODULE.md (email/nickname/senha
    ainda não têm fluxo de troca implementado no backend original)."""

    class Meta:
        model = User
        fields = ["name", "height"]

    def clean_height(self):
        height = self.cleaned_data["height"]
        if height < 50 or height > 300:
            raise ValidationError("Altura deve estar entre 50 e 300 cm.")
        return height
