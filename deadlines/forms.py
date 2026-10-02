from django import forms

from .models import Deadline


class DeadlineForm(forms.ModelForm):
    class Meta:
        model = Deadline
        fields = ('title', 'details', 'due_date')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }