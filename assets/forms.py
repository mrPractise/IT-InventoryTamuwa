from django import forms
from .models import Asset, Category, StatusOption, Department, Person


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'asset_id', 'category', 'model_description', 'serial_number',
            'purchase_date', 'purchased_from', 'purchase_cost',
            'assigned_to', 'department', 'status',
            'requisition', 'admin_comments'
        ]
        widgets = {
            'asset_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'model_description': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'purchased_from': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor / supplier name'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'requisition': forms.Select(attrs={'class': 'form-control'}),
            'admin_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from requisition.models import Requisition
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['status'].queryset = StatusOption.objects.filter(is_active=True)
        self.fields['assigned_to'].queryset = Person.objects.all().order_by('first_name', 'last_name')
        self.fields['department'].queryset = Department.objects.all().order_by('name')
        self.fields['requisition'].queryset = Requisition.objects.all().order_by('-created_at')
        self.fields['assigned_to'].required = False
        self.fields['department'].required = False
        self.fields['purchase_date'].required = False
        self.fields['purchased_from'].required = False
        self.fields['purchase_cost'].required = False
        self.fields['requisition'].required = False
        self.fields['asset_id'].required = False
