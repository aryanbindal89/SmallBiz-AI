from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError

from compliance.models import ComplianceRequirement
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    def __init__(self, *args, owner=None, required_requirement=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner is None:
            self.fields['requirement'].queryset = ComplianceRequirement.objects.none()
        else:
            self.fields['requirement'].queryset = ComplianceRequirement.objects.filter(
                applications__owner=owner,
            ).distinct()
        if required_requirement is not None:
            self.fields['requirement'].queryset = ComplianceRequirement.objects.filter(
                pk=required_requirement.pk,
            )
            self.fields['requirement'].initial = required_requirement.pk
            self.fields['requirement'].disabled = True

    class Meta:
        model = Document
        fields = ('title', 'category', 'requirement', 'issue_date', 'expiry_date', 'file')
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')
        if issue_date and expiry_date and expiry_date < issue_date:
            self.add_error('expiry_date', 'Expiry date cannot be before the issue date.')
        return cleaned_data

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        allowed_extensions = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'}
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in allowed_extensions:
            raise ValidationError('Upload a PDF, Word document, JPG, or PNG file.')
        if uploaded_file.size > 10 * 1024 * 1024:
            raise ValidationError('The maximum file size is 10 MB.')
        return uploaded_file


class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('title', 'category', 'issue_date', 'expiry_date')
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')
        if issue_date and expiry_date and expiry_date < issue_date:
            self.add_error('expiry_date', 'Expiry date cannot be before the issue date.')
        return cleaned_data