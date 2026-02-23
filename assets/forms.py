from django import forms
from .models import Asset, Category, StatusOption, Department
from django.contrib.auth.models import User


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'asset_id', 'category', 'model_description', 'serial_number',
            'purchase_date', 'assigned_to', 'department', 'status',
            'admin_comments'
        ]
        widgets = {
            'asset_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'model_description': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/yyyy'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'admin_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['status'].queryset = StatusOption.objects.filter(is_active=True)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('username')
        self.fields['department'].queryset = Department.objects.all().order_by('name')
        self.fields['assigned_to'].required = False
        self.fields['department'].required = False
        self.fields['purchase_date'].required = False
        self.fields['asset_id'].required = False
