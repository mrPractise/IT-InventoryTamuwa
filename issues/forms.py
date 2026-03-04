from django import forms
from .models import Issue, Project
from assets.models import Asset, Department, Category


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['title', 'description', 'priority', 'status', 'asset', 'department']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'asset': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(is_deleted=False).order_by('asset_id')
        self.fields['asset'].required = False
        self.fields['department'].queryset = Department.objects.all().order_by('name')
        self.fields['department'].required = False
        self.fields['description'].required = False


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'date', 'problem_statement',
            'cost_breakdown', 'conclusion', 'priority', 'status',
            'pending_reason', 'rejected_reason', 'categories',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'problem_statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'cost_breakdown': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'e.g.\nMonitors x5 @ KES 20,000 = KES 100,000\nKeyboards x5 @ KES 2,000 = KES 10,000'
            }),
            'conclusion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'pending_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'rejected_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'categories': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['date'].required = False
        self.fields['problem_statement'].required = False
        self.fields['cost_breakdown'].required = False
        self.fields['conclusion'].required = False
        self.fields['pending_reason'].required = False
        self.fields['rejected_reason'].required = False
        self.fields['categories'].required = False
        self.fields['categories'].queryset = Category.objects.all().order_by('name')

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        if status == 'Rejected' and not cleaned.get('rejected_reason'):
            self.add_error('rejected_reason', 'A reason is required when rejecting a project.')
        return cleaned


class CommentForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Add a comment or progress update...'
        }),
        label='Comment'
    )
