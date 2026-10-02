from django.conf import settings
from django.db import models

from businesses.models import BUSINESS_TYPE_CHOICES


class ComplianceRequirement(models.Model):
	name = models.CharField(max_length=160)
	business_type = models.CharField(
		max_length=40,
		choices=[('', 'Any business type'), *BUSINESS_TYPE_CHOICES],
		blank=True,
	)
	country = models.CharField(max_length=80, blank=True)
	state = models.CharField(max_length=80, blank=True)
	city = models.CharField(max_length=80, blank=True)
	minimum_employees = models.PositiveIntegerField(null=True, blank=True)
	maximum_employees = models.PositiveIntegerField(null=True, blank=True)
	summary = models.CharField(max_length=300)
	why_required = models.TextField()
	documents_needed = models.TextField()
	application_steps = models.TextField()
	official_source_url = models.URLField()
	official_portal_url = models.URLField()
	is_active = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class RequirementApplication(models.Model):
	class Status(models.TextChoices):
		APPLIED = 'applied', 'Applied'
		DOCUMENT_UPLOADED = 'document_uploaded', 'Document uploaded'

	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requirement_applications')
	requirement = models.ForeignKey(ComplianceRequirement, on_delete=models.CASCADE, related_name='applications')
	status = models.CharField(max_length=24, choices=Status.choices, default=Status.APPLIED)
	applied_at = models.DateTimeField()
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['owner', 'requirement'], name='unique_user_requirement_application'),
		]

	def __str__(self):
		return f'{self.owner} - {self.requirement}'
