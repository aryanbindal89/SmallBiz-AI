from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from businesses.models import BusinessProfile

from .models import ComplianceRequirement, RequirementApplication


class ComplianceWorkflowTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username='compliance-user',
			password='test-password',
		)
		self.profile = BusinessProfile.objects.create(
			owner=self.user,
			business_name='Bengaluru Shop',
			business_type='retail',
			country='India',
			state='Karnataka',
			city='Bengaluru',
			employee_count=4,
		)
		self.requirement = self.create_requirement('Retail registration', 'retail')

	def create_requirement(self, name, business_type, **overrides):
		values = {
			'name': name,
			'business_type': business_type,
			'country': 'India',
			'state': 'Karnataka',
			'city': 'Bengaluru',
			'summary': f'{name} may apply to this business.',
			'why_required': 'It records the business with the relevant authority.',
			'documents_needed': 'Identity and address proof.',
			'application_steps': 'Complete the form on the official portal.',
			'official_source_url': 'https://example.gov.in/source',
			'official_portal_url': 'https://example.gov.in/apply',
		}
		values.update(overrides)
		return ComplianceRequirement.objects.create(**values)

	def test_profile_form_matches_requirements_by_type_and_location(self):
		other_requirement = self.create_requirement('Food business registration', 'food_service')
		self.profile.delete()
		self.client.force_login(self.user)

		response = self.client.post(reverse('ai_assistant'), {
			'action': 'save_profile',
			'business_name': 'New Bengaluru Shop',
			'business_type': 'retail',
			'business_activity': 'Clothing sales',
			'country': 'India',
			'state': 'Karnataka',
			'city': 'Bengaluru',
			'employee_count': '4',
		})

		self.assertRedirects(response, reverse('ai_assistant'))
		self.assertEqual(BusinessProfile.objects.get(owner=self.user).business_name, 'New Bengaluru Shop')
		response = self.client.get(reverse('ai_assistant'))
		self.assertContains(response, 'Tell us about your business')
		self.assertContains(response, self.requirement.name)
		self.assertNotContains(response, other_requirement.name)

	def test_requirement_detail_shows_official_links_and_marks_application(self):
		self.client.force_login(self.user)
		detail_url = reverse('compliance:requirement_detail', args=[self.requirement.pk])

		response = self.client.get(detail_url)

		self.assertContains(response, 'Why it may be required')
		self.assertContains(response, 'Documents you may need')
		self.assertContains(response, 'How to apply')
		self.assertContains(response, 'https://example.gov.in/source')
		self.assertContains(response, 'https://example.gov.in/apply')
		self.assertContains(response, 'does not submit it for you')

		response = self.client.post(detail_url)

		self.assertRedirects(
			response,
			reverse('documents:upload_for_requirement', args=[self.requirement.pk]),
		)
		application = RequirementApplication.objects.get(owner=self.user, requirement=self.requirement)
		self.assertEqual(application.status, RequirementApplication.Status.APPLIED)

	def test_user_cannot_open_a_requirement_outside_their_profile_match(self):
		unmatched = self.create_requirement('Food registration', 'food_service')
		self.client.force_login(self.user)

		response = self.client.get(reverse('compliance:requirement_detail', args=[unmatched.pk]))

		self.assertEqual(response.status_code, 404)
