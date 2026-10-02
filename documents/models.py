from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


def document_upload_path(instance, filename):
	return f'private_documents/user_{instance.owner_id}/{timezone.now():%Y/%m}/{Path(filename).name}'


class Document(models.Model):
	class Category(models.TextChoices):
		LICENSE = 'license', 'Licence or registration'
		TAX = 'tax', 'Tax document'
		IDENTITY = 'identity', 'Identity document'
		OTHER = 'other', 'Other'

	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
	requirement = models.ForeignKey(
		'compliance.ComplianceRequirement',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='documents',
	)
	title = models.CharField(max_length=150)
	category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
	file = models.FileField(upload_to=document_upload_path)
	issue_date = models.DateField(null=True, blank=True)
	expiry_date = models.DateField(null=True, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-uploaded_at']

	def __str__(self):
		return self.title
