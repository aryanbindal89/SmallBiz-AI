from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from documents.models import Document


class DeadlineFlowTests(TestCase):
	def setUp(self):
		self.owner = get_user_model().objects.create_user(username='deadline-owner', password='test-password')
		self.other_user = get_user_model().objects.create_user(username='deadline-other', password='test-password')

	def test_deadline_page_requires_login(self):
		response = self.client.get(reverse('deadlines:list'))

		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response.url)

	def test_page_shows_only_owned_expired_and_next_ten_day_documents(self):
		today = timezone.localdate()
		expired = Document.objects.create(
			owner=self.owner,
			title='Expired licence',
			file='expired-licence.pdf',
			expiry_date=today - timedelta(days=1),
		)
		due_today = Document.objects.create(
			owner=self.owner,
			title='Expires today',
			file='expires-today.pdf',
			expiry_date=today,
		)
		due_tomorrow = Document.objects.create(
			owner=self.owner,
			title='Expires tomorrow',
			file='expires-tomorrow.pdf',
			expiry_date=today + timedelta(days=1),
		)
		due_in_ten_days = Document.objects.create(
			owner=self.owner,
			title='Expires in ten days',
			file='expires-in-ten-days.pdf',
			expiry_date=today + timedelta(days=10),
		)
		Document.objects.create(
			owner=self.owner,
			title='Expires later',
			file='expires-later.pdf',
			expiry_date=today + timedelta(days=11),
		)
		Document.objects.create(
			owner=self.owner,
			title='No expiry date',
			file='no-expiry.pdf',
		)
		Document.objects.create(
			owner=self.other_user,
			title='Other user document',
			file='other-user.pdf',
			expiry_date=today + timedelta(days=1),
		)
		self.client.force_login(self.owner)

		response = self.client.get(reverse('deadlines:list'))

		self.assertEqual(list(response.context['action_documents']), [expired, due_today])
		self.assertEqual(
			list(response.context['expiring_documents']),
			[due_tomorrow, due_in_ten_days],
		)
		self.assertContains(response, 'Expired or expiring today')
		self.assertContains(response, 'Expires today')
		self.assertContains(response, 'Expiring within 10 days')
		self.assertNotContains(response, 'Expires later')
		self.assertNotContains(response, 'No expiry date')
		self.assertNotContains(response, 'Other user document')

# Create your tests here.
