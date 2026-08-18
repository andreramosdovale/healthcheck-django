from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect("measurements:list")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.terms_accepted = True
            user.terms_accepted_at = timezone.now()
            user.save()

            user_group, _ = Group.objects.get_or_create(name="user")
            user.groups.add(user_group)

            auth_login(request, user, backend="accounts.backends.EmailOrNicknameBackend")
            messages.success(request, "Conta criada com sucesso.")
            return redirect("measurements:list")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("measurements:list")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["login"]
            password = form.cleaned_data["password"]

            try:
                user = User.objects.get(Q(email=identifier) | Q(nickname=identifier))
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

            if user is None or not user.check_password(password):
                # Não revela se o email/nickname existe (mesma regra do AUTH_MODULE.md).
                form.add_error(None, "Credenciais inválidas.")
            elif not user.is_active:
                form.add_error(None, "Esta conta está inativa.")
            else:
                auth_login(request, user, backend="accounts.backends.EmailOrNicknameBackend")
                return redirect("measurements:list")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})
