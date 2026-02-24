from django import forms
from django.forms import inlineformset_factory
from .models import Requisition, RequisitionItem


class RequisitionForm(forms.ModelForm):
    class Meta:
        model = Requisition
        fields = ['req_no', 'title', 'description', 'status']
        widgets = {
            'req_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. REQ-001 (from physical book)'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Requisition title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Summary or description of this requisition'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class RequisitionItemForm(forms.ModelForm):
    class Meta:
        model = RequisitionItem
        fields = ['item_name', 'unit_price', 'quantity', 'is_approved', 'rejection_reason']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item or service description'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control item-unit-price', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control item-quantity', 'min': '1', 'placeholder': '1'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input item-approved', 'title': 'Approved'}),
            'rejection_reason': forms.TextInput(attrs={'class': 'form-control item-reason', 'placeholder': 'Reason (if not approved)'}),
        }


RequisitionItemFormSet = inlineformset_factory(
    Requisition,
    RequisitionItem,
    form=RequisitionItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
