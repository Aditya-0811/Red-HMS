from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.html import mark_safe
from shortuuid.django_fields import ShortUUIDField

GENDER = (("Male","Male"),("Female","Female"),("Other","Other"))
IDENTITY = (("National ID","National ID"),("Passport","Passport"),("Driver Licence","Driver Licence"))
ROLES   = (("Admin","Admin"),("Manager","Manager"),("Receptionist","Receptionist"),
           ("Housekeeping","Housekeeping"),("Guest","Guest"))

class User(AbstractUser):
    uid   = ShortUUIDField(unique=True, length=10, max_length=20,
                           alphabet="abcdefghijklmnopqrstuvwxyz1234567890")
    email = models.EmailField(unique=True)
    role  = models.CharField(max_length=20, choices=ROLES, default="Guest")
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_staff_member(self):
        return self.role in ("Admin","Manager","Receptionist","Housekeeping")


class Profile(models.Model):
    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image         = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    full_name     = models.CharField(max_length=200, null=True, blank=True)
    phone         = models.CharField(max_length=30,  null=True, blank=True)
    gender        = models.CharField(max_length=10,  choices=GENDER,   null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country       = models.CharField(max_length=100, null=True, blank=True)
    state         = models.CharField(max_length=100, null=True, blank=True)
    city          = models.CharField(max_length=100, null=True, blank=True)
    address       = models.CharField(max_length=300, null=True, blank=True)
    identity_type  = models.CharField(max_length=30, choices=IDENTITY, null=True, blank=True)
    identity_image = models.ImageField(upload_to='identity_docs/', null=True, blank=True)
    facebook      = models.URLField(null=True, blank=True)
    twitter       = models.URLField(null=True, blank=True)
    wallet        = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    date_joined   = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def thumbnail(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="40" height="40" style="border-radius:50%;object-fit:cover;">')
        return "No Image"
    thumbnail.short_description = "Avatar"


class Notification(models.Model):
    TYPES = (
        ("Booking Confirmed","Booking Confirmed"),
        ("Booking Cancelled","Booking Cancelled"),
        ("Payment Received","Payment Received"),
        ("Check-In Reminder","Check-In Reminder"),
        ("General","General"),
    )
    user    = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='notifications', null=True, blank=True)
    type    = models.CharField(max_length=100, choices=TYPES, default="General")
    message = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    date    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.type} → {self.user}"
