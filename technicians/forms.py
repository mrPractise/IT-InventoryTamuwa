from django import forms
from .models import Technician, TechnicianAssistant, TechnicianService, TechnicianRecommendation


class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ['company_name', 'technician_name', 'email', 'phone_number', 'alternate_phone', 
                  'address', 'specialization', 'is_active']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'technician_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Laptop Repair, Network Installation'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TechnicianAssistantForm(forms.ModelForm):
    class Meta:
        model = TechnicianAssistant
        fields = ['name', 'phone_number', 'email', 'role', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Junior Technician, Helper'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TechnicianServiceForm(forms.ModelForm):
    class Meta:
        model = TechnicianService
        fields = ['service_name', 'description', 'typical_cost', 'is_active']
        widgets = {
            'service_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'typical_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TechnicianRecommendationForm(forms.ModelForm):
    class Meta:
        model = TechnicianRecommendation
        fields = ['technician', 'category_name', 'recommendation_type', 'description', 'estimated_cost', 'priority', 'notes']
        widgets = {
            'technician': forms.Select(attrs={'class': 'form-control'}),
            'category_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Laptops, Printers, Network Switch'}),
            'recommendation_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
