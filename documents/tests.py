from datetime import timedelta
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from compliance.models import ComplianceRequirement, RequirementApplication

from .models import Document


class DocumentFlowTests(TestCase):
	def setUp(self):
		self.media = TemporaryDirectory()
		self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
		self.settings_override.enable()
		user_model = get_user_model()
		self.owner = user_model.objects.create_user(username='owner', password='test-password')
		self.other_user = user_model.objects.create_user(username='other', password='test-password')

	def tearDown(self):
		self.settings_override.disable()
		self.media.cleanup()

	def test_document_page_requires_login(self):
		response = self.client.get(reverse('documents:list'))

		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response.url)

	def test_user_can_upload_and_download_document(self):
		self.client.force_login(self.owner)
		response = self.client.post(reverse('documents:list'), {
			'title': 'Shop licence',
			'category': Document.Category.LICENSE,
			'file': SimpleUploadedFile('licence.pdf', b'%PDF test content', content_type='application/pdf'),
			'issue_date': (timezone.localdate() - timedelta(days=10)).isoformat(),
			'expiry_date': (timezone.localdate() + timedelta(days=10)).isoformat(),
		})

		self.assertRedirects(response, reverse('documents:list'))
		document = Document.objects.get(owner=self.owner)
		self.assertIn(f'user_{self.owner.pk}', document.file.name)
		self.assertEqual(document.issue_date, timezone.localdate() - timedelta(days=10))
		self.assertEqual(document.expiry_date, timezone.localdate() + timedelta(days=10))

		download = self.client.get(reverse('documents:download', args=[document.pk]))
		self.assertEqual(download.status_code, 200)
		self.assertIn('attachment', download['Content-Disposition'])
		self.assertEqual(b''.join(download.streaming_content), b'%PDF test content')

	def test_expiry_date_is_optional_for_new_uploads(self):
		self.client.force_login(self.owner)
		response = self.client.post(reverse('documents:list'), {
			'title': 'Undated licence',
			'category': Document.Category.LICENSE,
			'file': SimpleUploadedFile('undated.pdf', b'%PDF test content'),
		})

		self.assertRedirects(response, reverse('documents:list'))
		self.assertIsNone(Document.objects.get(owner=self.owner).expiry_date)

	def test_other_user_cannot_view_or_download_document(self):
		document = Document.objects.create(
			owner=self.owner,
			title='Private licence',
			category=Document.Category.LICENSE,
			file=SimpleUploadedFile('private.pdf', b'%PDF private'),
		)
		self.client.force_login(self.other_user)

		response = self.client.get(reverse('documents:list'))
		self.assertNotContains(response, 'Private licence')
		self.assertEqual(self.client.get(reverse('documents:download', args=[document.pk])).status_code, 404)
		self.assertEqual(self.client.get(reverse('documents:edit', args=[document.pk])).status_code, 404)

	def test_owner_can_edit_issue_and_expiry_dates(self):
		document = Document.objects.create(
			owner=self.owner,
			title='Shop licence',
			file='shop-licence.pdf',
		)
		self.client.force_login(self.owner)
		issue_date = timezone.localdate() - timedelta(days=2)
		expiry_date = timezone.localdate() + timedelta(days=20)

		response = self.client.post(reverse('documents:edit', args=[document.pk]), {
			'title': document.title,
			'category': document.category,
			'issue_date': issue_date.isoformat(),
			'expiry_date': expiry_date.isoformat(),
		})

		self.assertRedirects(response, reverse('documents:list'))
		document.refresh_from_db()
		self.assertEqual(document.issue_date, issue_date)
		self.assertEqual(document.expiry_date, expiry_date)

	def test_requirement_application_upload_links_document_and_updates_status(self):
		requirement = ComplianceRequirement.objects.create(
			name='Retail registration',
			business_type='retail',
			country='India',
			state='Karnataka',
			city='Bengaluru',
			summary='Register a retail business.',
			why_required='Local rules may require registration.',
			documents_needed='Identity proof',
			application_steps='Submit the form on the official portal.',
			official_source_url='https://example.gov.in/source',
			official_portal_url='https://example.gov.in/apply',
		)
		application = RequirementApplication.objects.create(
			owner=self.owner,
			requirement=requirement,
			applied_at=timezone.now(),
		)
		self.client.force_login(self.owner)
		response = self.client.post(reverse('documents:upload_for_requirement', args=[requirement.pk]), {
			'title': 'Retail certificate',
			'category': Document.Category.LICENSE,
			'issue_date': timezone.localdate().isoformat(),
			'file': SimpleUploadedFile('retail-certificate.pdf', b'%PDF certificate'),
		})

		self.assertRedirects(response, reverse('documents:list'))
		document = Document.objects.get(owner=self.owner)
		self.assertEqual(document.requirement, requirement)
		application.refresh_from_db()
		self.assertEqual(application.status, RequirementApplication.Status.DOCUMENT_UPLOADED)

	def test_rejects_unsupported_file_extension(self):
		self.client.force_login(self.owner)
		response = self.client.post(reverse('documents:list'), {
			'title': 'Unexpected file',
			'category': Document.Category.OTHER,
			'file': SimpleUploadedFile('payload.exe', b'not a document'),
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Upload a PDF, Word document, JPG, or PNG file.')
		self.assertFalse(Document.objects.exists())
