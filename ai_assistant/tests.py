from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from businesses.models import BusinessProfile
from compliance.models import ComplianceRequirement

from .formatting import parse_assistant_response


class AiAssistantTests(TestCase):
    def test_assistant_links_to_user_documents(self):
        user = get_user_model().objects.create_user(username='assistant-user', password='test-password')
        self.client.force_login(user)

        response = self.client.get(reverse('ai_assistant'))

        self.assertContains(response, 'My documents')
        self.assertContains(response, reverse('documents:list'))

    def test_ai_assistant_page_requires_login(self):
        response = self.client.get(reverse('ai_assistant'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_ai_response_is_split_into_sections_lists_and_keywords(self):
        response = '## Short answer\nRegister if required.\n\n## Action checklist\n1. Check your turnover.\n- Verify with an official source.\n\n## Key terms\n- **GST**: Goods and Services Tax.'

        sections, keywords = parse_assistant_response(response)

        self.assertEqual([section['title'] for section in sections], ['Short answer', 'Action checklist'])
        self.assertEqual(sections[1]['blocks'][0]['type'], 'list')
        self.assertIn('GST', keywords)
        self.assertNotIn('Key terms', [section['title'] for section in sections])

    @patch('ai_assistant.views.explain_business_requirement', return_value='## Short answer\nCheck the renewal date.\n\n## Action checklist\n1. Confirm the issuing authority.')
    def test_ai_page_renders_a_structured_answer(self, explain_requirement):
        user = get_user_model().objects.create_user(username='assistant-user', password='test-password')
        BusinessProfile.objects.create(
            owner=user,
            business_name='Test Shop',
            business_type='retail',
            country='India',
            state='Karnataka',
            city='Bengaluru',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('ai_assistant'), {'question': 'How do I renew a licence?'})

        self.assertContains(response, 'Short answer')
        self.assertContains(response, 'Action checklist')
        self.assertContains(response, 'Confirm the issuing authority.')
        explain_requirement.assert_called_once()

    @patch('ai_assistant.views.explain_business_requirement', return_value='## Short answer\nReview matched requirements.')
    def test_ai_response_separates_licences_from_official_platforms(self, explain_requirement):
        user = get_user_model().objects.create_user(username='assistant-user', password='test-password')
        BusinessProfile.objects.create(
            owner=user,
            business_name='Test Shop',
            business_type='retail',
            country='India',
            state='Karnataka',
            city='Bengaluru',
        )
        requirement = ComplianceRequirement.objects.create(
            name='Retail registration',
            business_type='retail',
            country='India',
            state='Karnataka',
            city='Bengaluru',
            summary='Register the retail business.',
            why_required='Local rules may require registration.',
            documents_needed='Identity proof.',
            application_steps='Apply through the portal.',
            official_source_url='https://example.gov.in/source',
            official_portal_url='https://example.gov.in/apply',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('ai_assistant'), {'question': 'Which licences do I need?'})
        rendered = response.content.decode()

        self.assertContains(response, 'Licences, registrations, and permits')
        self.assertContains(response, requirement.name)
        self.assertContains(response, 'Official application platforms')
        self.assertContains(response, requirement.official_portal_url)
        self.assertLess(rendered.index('Licences, registrations, and permits'), rendered.index('Official application platforms'))

    @patch('ai_assistant.views.explain_business_requirement', side_effect=RuntimeError('provider internals'))
    def test_ai_provider_error_is_user_friendly(self, explain_requirement):
        user = get_user_model().objects.create_user(username='assistant-user', password='test-password')
        BusinessProfile.objects.create(
            owner=user,
            business_name='Test Shop',
            business_type='retail',
            country='India',
            state='Karnataka',
            city='Bengaluru',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('ai_assistant'), {'question': 'How do I renew a licence?'})

        self.assertContains(response, 'The assistant is temporarily unavailable.')
        self.assertNotContains(response, 'provider internals')
