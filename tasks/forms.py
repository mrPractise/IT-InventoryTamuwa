from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        from users.models import UserProfile
        # Get all active users with their profiles, ordered by role and username
        users = User.objects.filter(is_active=True).select_related('profile').order_by('username')
        # Create choices with role labels
        choices = [('', '--- Select User ---')]
        for user in users:
            role = getattr(user.profile, 'role', 'viewer') if hasattr(user, 'profile') else 'viewer'
            role_display = dict(UserProfile.ROLE_CHOICES).get(role, 'Viewer')
            choices.append((user.id, f"{user.get_full_name() or user.username} ({role_display})"))
        
        self.fields['assigned_to'].queryset = users
        self.fields['assigned_to'].choices = choices
        self.fields['assigned_to'].required = False
        self.fields['assigned_to'].label = "Assigned To (User)"
        self.fields['due_date'].required = False
        self.fields['description'].required = False
