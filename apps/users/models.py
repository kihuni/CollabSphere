from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .managers import CustomUserManager

class Role(models.Model):
    """
    Role model for user permissions
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Define permissions for each role
    can_moderate = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_roles = models.BooleanField(default=False)
    can_delete_messages = models.BooleanField(default=False)
    can_ban_users = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model for CollabSphere.
    """
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'), max_length=50, unique=True)
    full_name = models.CharField(_('full name'), max_length=255)
    
    # Profile fields
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    
    # Status fields
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    # Role field
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Verification fields
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    verification_token_created = models.DateTimeField(null=True, blank=True)
    
    # Required fields
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']

    def generate_verification_token(self):
        self.verification_token = get_random_string(64)
        self.verification_token_created = timezone.now()
        self.save()
        return self.verification_token

    def send_verification_email(self):
        token = self.generate_verification_token()
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        
        context = {
            'user': self,
            'verification_url': verification_url
        }
        
        message = render_to_string('email/verify_email.html', context)
        
        send_mail(
            'Verify your email address',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=message,
            fail_silently=False,
        )

    def check_role_permission(self, permission):
        """
        Check if user has specific permission based on their role
        """
        if not self.role:
            return False
        return getattr(self.role, permission, False)