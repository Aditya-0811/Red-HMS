from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile

INPUT = 'with-border'   # reference stylesheet class

class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=200, required=True,
        widget=forms.TextInput(attrs={'class':INPUT,'placeholder':'Full Name'}))
    username  = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class':INPUT,'placeholder':'Username'}))
    email     = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class':INPUT,'placeholder':'Email Address'}))
    password1 = forms.CharField(required=True,
        widget=forms.PasswordInput(attrs={'class':INPUT,'placeholder':'Password'}))
    password2 = forms.CharField(required=True,
        widget=forms.PasswordInput(attrs={'class':INPUT,'placeholder':'Confirm Password'}))

    class Meta:
        model  = User
        fields = ['full_name','username','email','password1','password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role  = 'Guest'
        if commit:
            user.save()
            Profile.objects.filter(user=user).update(
                full_name=self.cleaned_data.get('full_name',''))
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['username','email']
        widgets = {
            'username': forms.TextInput(attrs={'class':INPUT}),
            'email':    forms.EmailInput(attrs={'class':INPUT}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = ['image','full_name','phone','gender','date_of_birth',
                  'country','state','city','address',
                  'identity_type','identity_image','facebook','twitter']
        widgets = {
            'image':         forms.FileInput(attrs={'class':'upload','onchange':'loadFile(event)'}),
            'full_name':     forms.TextInput(attrs={'class':INPUT}),
            'phone':         forms.TextInput(attrs={'class':INPUT}),
            'gender':        forms.Select(attrs={'class':INPUT}),
            'date_of_birth': forms.DateInput(attrs={'class':INPUT,'type':'date'}),
            'country':       forms.TextInput(attrs={'class':INPUT}),
            'state':         forms.TextInput(attrs={'class':INPUT}),
            'city':          forms.TextInput(attrs={'class':INPUT}),
            'address':       forms.Textarea(attrs={'class':INPUT,'rows':3}),
            'identity_type': forms.Select(attrs={'class':INPUT}),
            'identity_image':forms.FileInput(attrs={'class':INPUT}),
            'facebook':      forms.URLInput(attrs={'class':INPUT}),
            'twitter':       forms.URLInput(attrs={'class':INPUT}),
        }


class ChangePasswordForm(forms.Form):
    old_password  = forms.CharField(widget=forms.PasswordInput(attrs={'class':INPUT,'placeholder':'Current Password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':INPUT,'placeholder':'New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':INPUT,'placeholder':'Confirm New Password'}))

    def clean(self):
        cd = super().clean()
        if cd.get('new_password1') != cd.get('new_password2'):
            raise forms.ValidationError("New passwords do not match.")
        return cd
