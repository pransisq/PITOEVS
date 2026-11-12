from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager


class VoterManager(BaseUserManager):
    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError(_("Username must be set"))
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        if password is None:
            password = username
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", 1)
        extra_fields.setdefault("last_name", "")
        extra_fields.setdefault("first_name", "")
        extra_fields.setdefault("company", "Palompon Institute of Technology")
        extra_fields.setdefault("address", "Evangelista St. Palompon, Leyte")
        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(username, password, **extra_fields)


