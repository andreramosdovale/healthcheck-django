import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

NICKNAME_VALIDATOR = RegexValidator(
    regex=r"^[a-zA-Z0-9_]+$",
    message="O nickname só pode conter letras, números e underscore.",
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, nickname, password, **extra_fields):
        if not email:
            raise ValueError("O email é obrigatório.")
        if not nickname:
            raise ValueError("O nickname é obrigatório.")
        email = self.normalize_email(email)
        user = self.model(email=email, nickname=nickname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, nickname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, nickname, password, **extra_fields)

    def create_superuser(self, email, nickname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("name", nickname)
        extra_fields.setdefault("birth_date", timezone.now().date())
        extra_fields.setdefault("sex", User.Sex.MALE)
        extra_fields.setdefault("height", 170)
        extra_fields.setdefault("terms_accepted", True)
        extra_fields.setdefault("terms_accepted_at", timezone.now())

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser precisa de is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa de is_superuser=True.")

        return self._create_user(email, nickname, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Sex(models.TextChoices):
        MALE = "male", "Masculino"
        FEMALE = "female", "Feminino"

    class Plan(models.TextChoices):
        FREE = "free", "Free"
        PREMIUM = "premium", "Premium"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=256, unique=True)
    nickname = models.CharField(
        max_length=30,
        unique=True,
        validators=[NICKNAME_VALIDATOR],
        help_text="3-30 caracteres, letras/números/underscore.",
    )
    name = models.CharField(max_length=100)
    birth_date = models.DateField()
    sex = models.CharField(max_length=6, choices=Sex.choices)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    plan = models.CharField(max_length=7, choices=Plan.choices, default=Plan.FREE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "nickname"
    REQUIRED_FIELDS = ["email", "name", "birth_date", "sex", "height"]

    def __str__(self):
        return self.nickname

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
