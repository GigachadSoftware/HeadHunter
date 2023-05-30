from datetime import datetime

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, UserManager
from django.db import models
from django.utils import timezone

from home.tests import get_city_name

ROLES = (
    ("W", "Робітник"),
    ("E", "Роботодавець"),
    ("S", "Суперкористувач"),
)

WORK_TYPES = (
    ("R", "Дистанційна"),
    ("F", "Повна зайнятість"),
    ("P", "Часткова зайнятість"),
    ("N", "Фріланс"),
)


EDUCATIONS = (
    ("E", "Дошкільна"),
    ("D", "Повна загальна середня"),
    ("C", "Професійна"),
    ("B", "Фахова передвища"),
    ("A", "Вища"),
)

EDUCATIONS_MAP = {
    "E": "Дошкільна",
    "D": "Повна загальна середня",
    "C": "Професійна",
    "B": "Фахова передвища",
    "A": "Вища",
}


class CustomUserManager(BaseUserManager):
    def _create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number=None,
        city=None,
        birthday=None,
        photo: str | None = None,
        **kwargs,
    ) -> "User":
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            city=city,
            birthday=birthday,
            photo=photo,
            **kwargs,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email,
        password,
        first_name,
        last_name,
        phone_number=None,
        city=None,
        birthday=None,
        photo=None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(
            email,
            password,
            first_name,
            last_name,
            phone_number,
            city,
            birthday,
            photo,
            **extra_fields,
        )

    def create_superuser(
        self,
        email,
        password,
        first_name,
        last_name,
        phone_number=None,
        city=None,
        birthday=None,
        photo=None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(
            email,
            password,
            first_name,
            last_name,
            phone_number,
            city,
            birthday,
            photo,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(db_index=True, unique=True, max_length=256)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=16, null=True, blank=True)
    city = models.CharField(max_length=64, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    photo = models.CharField(max_length=512, null=True, blank=True)
    role = models.CharField(max_length=1, choices=ROLES, default="W")

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    # + password
    # + last_login
    # + is_active

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number", "city", "birthday"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def get_city(self):
        return get_city_name(str(self.city))

    def get_birthday(self):
        return self.birthday.strftime("%Y-%m-%d")


class Vacancy(models.Model):
    objects = models.Manager()
    title = models.CharField(max_length=128)
    city = models.CharField(max_length=64)
    type = models.CharField(max_length=1, choices=WORK_TYPES)
    creation_time = models.DateTimeField(auto_created=True)
    looking_for = models.CharField(max_length=32, default="Unknown")
    description = models.TextField()
    thumbnail = models.CharField(max_length=512, null=True, blank=True)
    publisher = models.EmailField()
    candidates = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return f"<{self.publisher}> {self.title}"

    class Meta:
        verbose_name = "Vacancy"
        verbose_name_plural = "Vacancies"

    def get_city(self):
        return get_city_name(str(self.city))

    def get_type(self):
        return [i for i in WORK_TYPES if i[0] == str(self.type)][0][1]

    def get_candidates(self):
        return [User.objects.filter(id=_id.id).first().email for _id in self.candidates.all()]


class Summary(models.Model):
    education = models.CharField(max_length=1, choices=EDUCATIONS)
    profession = models.CharField(max_length=64)
    end_of_education = models.DateField()
    skills = models.CharField(max_length=256)
    city = models.CharField(max_length=64)
    views = models.TextField(default="")
    user_id = models.BigIntegerField()

    def get_education(self):
        return EDUCATIONS_MAP.get(str(self.education))

    def get_city(self):
        return get_city_name(str(self.city))

    def get_view_count(self):
        return len(str(self.views).split(";"))

    def add_view(self, user_id: int):
        views = str(self.views).split(";")
        if str(user_id) not in views:
            self.views = ";".join([*views, str(user_id)])
            self.save()
