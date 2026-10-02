from django import forms

from .models import BusinessProfile


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = (
            'business_name',
            'business_type',
            'business_activity',
            'country',
            'state',
            'city',
            'employee_count',
        )
        widgets = {
            'employee_count': forms.NumberInput(attrs={'min': 0}),
        }