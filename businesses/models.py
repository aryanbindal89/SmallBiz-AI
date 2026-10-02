from django.conf import settings
from django.db import models


BUSINESS_TYPE_CHOICES = [
	('retail', 'Retail'),
	('food_service', 'Food service'),
	('professional_services', 'Professional services'),
	('manufacturing', 'Manufacturing'),
	('other', 'Other'),
]


class BusinessProfile(models.Model):
	owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_profile')
	business_name = models.CharField(max_length=150)
	business_type = models.CharField(max_length=40, choices=BUSINESS_TYPE_CHOICES)
	business_activity = models.CharField(max_length=160, blank=True)
	country = models.CharField(max_length=80)
	state = models.CharField(max_length=80)
	city = models.CharField(max_length=80)
	employee_count = models.PositiveIntegerField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.business_name
