from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, department=None, is_admin=False):
        if not email:
            raise ValueError("Users must have an email address.")
        if not username:
            raise ValueError("Users must have a username.")
        if not department:
            raise ValueError("Users must belong to a department")
        
    
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            department=department,
            is_admin=is_admin
            )
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_admin(self, username, email, password, department="Finance Admin"):
        """Creates an admin user."""
        user = self.create_user(username, email, password, department, is_admin=True)
        user.is_staff = True # Ensure admin users are also staff users
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    department = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "department"]
    
    def save(self, *args, **kwargs):
        """Ensure admins have is_staff=True."""
        if self.is_admin:
            self.is_staff = True  # Only admin users get staff privileges
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        return self.is_admin  # Only admins can have special permissions

    def has_module_perms(self, app_label):
        return self.is_admin  # Only admins can access admin-related modules

    def __str__(self):
        return f"{self.username} ({'Admin' if self.is_admin else 'End User'})"