from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from assets.models import Department, Person
from .models import UserProfile


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'department']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional description'}),
        }


class PasswordChangeRequiredForm(PasswordChangeForm):
    """Password change form for first login or forced password change"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove old password field for first login (they don't know it)
        if hasattr(self.user, 'profile') and self.user.profile.is_first_login:
            del self.fields['old_password']


class UserCreateForm(forms.ModelForm):
    """Form for creating new users by admin"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('technician', 'Technician'),
        ('viewer', 'Viewer'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='viewer'
    )
    temporary_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        initial='Welcome123!',
        help_text='User will be required to change this on first login.'
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['temporary_password'])
        
        if commit:
            user.save()
            # Create profile with role and force password change
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                is_first_login=True,
                must_change_password=True
            )
        
        return user


class UserEditForm(forms.ModelForm):
    """Form for editing existing users"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('technician', 'Technician'),
        ('viewer', 'Viewer'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['role'].initial = self.instance.profile.role
            self.fields['is_active'].initial = self.instance.is_active
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            # Update profile
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.role = self.cleaned_data['role']
                profile.save()
        
        return user
