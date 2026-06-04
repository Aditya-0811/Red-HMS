from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from import_export.admin import ImportExportModelAdmin
from .models import User, Profile, Notification


class AdminUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email address')

    class Meta(UserCreationForm.Meta):
        model  = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin, ImportExportModelAdmin):
    add_form      = AdminUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields' : ('username', 'email', 'password1', 'password2'),
        }),
    )
    inlines       = [ProfileInline]
    list_display  = ['uid','username','email','role','is_active','date_joined']
    list_filter   = ['role','is_active','is_staff']
    search_fields = ['username','email','uid']
    list_editable = ['role','is_active']
    list_per_page = 50
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('Red HMS', {'fields': ('role','uid')}),
    )


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    list_display  = ['thumbnail','user','full_name','phone','city','country']
    search_fields = ['user__username','user__email','full_name']
    list_per_page = 50


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['type','user','is_read','date']
    list_filter   = ['type','is_read']
    list_editable = ['is_read']
    list_per_page = 50
