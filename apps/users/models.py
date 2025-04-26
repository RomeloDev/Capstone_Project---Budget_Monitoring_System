from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

# Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, username, fullname, email, password=None, department=None, **extra_fields):
        """Creates and returns a regular user."""
        if not email:
            raise ValueError("Users must have an email address.")
        if not username:
            raise ValueError("Users must have a username.")
        if not fullname:
            raise ValueError("Users must have a fullname.")
        if not department:
            raise ValueError("Users must belong to a department.")
        
        email = self.normalize_email(email)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_approving_officer", False)

        user = self.model(
            username=username,
            fullname=fullname,
            email=email,
            department=department,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        
        return user

    def create_superuser(self, email, username, fullname, department, password=None, **extra_fields):
        """Creates and returns a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_approving_officer", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, fullname, email, password, department, **extra_fields)

    def create_admin(self, username, fullname, email, password, department="Finance Admin"):
        """Creates and returns an admin user."""
        return self.create_user(username, fullname, email, password, department, is_staff=True, is_admin=True)

    def create_approving_officer(self, username, fullname, email, password, department="Campus Director"):
        """Creates and returns an approving officer user."""
        return self.create_user(username, fullname, email, password, department, is_approving_officer=True)
    
# Custom User Model
class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    fullname = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    department = models.CharField(max_length=255)

    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # Added this field   
    is_approving_officer = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "fullname", "department"]

    def save(self, *args, **kwargs):
        """Ensure admin users have correct permissions."""
        if self.is_admin:
            self.is_staff = True  # Admins should always be staff
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        """Returns True if the user has a specific permission."""
        return self.is_superuser  # Superusers have all permissions

    def has_module_perms(self, app_label):
        """Returns True if the user has permissions to view the app `app_label`."""
        return self.is_superuser  # Superusers can access all apps

    def __str__(self):
        return f"{self.username} ({'Superuser' if self.is_superuser else 'Admin' if self.is_admin else 'User'})"
