from django import forms
from .models import MaintenanceLog, ActionTakenOption
from assets.models import Asset

class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = [
            'asset', 'date_reported', 'date_completed', 'description', 
            'action_taken', 'cost_of_repair', 'maintenance_status', 'notes'
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-control'}),
            'date_reported': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/yyyy'}),
            'date_completed': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/yyyy'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'action_taken': forms.Select(attrs={'class': 'form-control'}),
            'cost_of_repair': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maintenance_status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(is_deleted=False).order_by('asset_id')
        self.fields['action_taken'].queryset = ActionTakenOption.objects.filter(is_active=True).order_by('name')
        self.fields['action_taken'].required = False
        self.fields['date_completed'].required = False
        self.fields['cost_of_repair'].required = False
        self.fields['notes'].required = False
