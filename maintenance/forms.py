from django import forms
from .models import MaintenanceLog, ActionTakenOption
from assets.models import Asset, Person


class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = [
            'asset', 'timestamp', 'date_reported', 'date_completed', 'description',
            'action_taken', 'cost_of_repair', 'maintenance_status',
            'performed_by', 'requisition', 'notes'
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-control'}),
            'timestamp': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'date_reported': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'date_completed': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'action_taken': forms.Select(attrs={'class': 'form-control'}),
            'cost_of_repair': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maintenance_status': forms.Select(attrs={'class': 'form-control'}),
            'performed_by': forms.Select(attrs={'class': 'form-control'}),
            'requisition': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from requisition.models import Requisition
        from technicians.models import Technician
        self.fields['asset'].queryset = Asset.objects.filter(is_deleted=False).order_by('asset_id')
        self.fields['action_taken'].queryset = ActionTakenOption.objects.filter(is_active=True).order_by('name')
        self.fields['performed_by'].queryset = Technician.objects.filter(is_active=True).order_by('company_name', 'technician_name')
        self.fields['requisition'].queryset = Requisition.objects.all().order_by('-created_at')
        self.fields['action_taken'].required = False
        self.fields['timestamp'].required = False
        self.fields['date_completed'].required = False
        self.fields['cost_of_repair'].required = False
        self.fields['performed_by'].required = False
        self.fields['requisition'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()
        date_reported = cleaned_data.get('date_reported')
        date_completed = cleaned_data.get('date_completed')
        if date_reported and date_completed and date_completed < date_reported:
            self.add_error(
                'date_completed',
                'Date completed cannot be before date reported.'
            )
        return cleaned_data
