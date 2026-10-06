import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase
from django.contrib.auth import get_user_model


class AccountFlowTests(TestCase):
	def test_bootstrap_admin_creates_superuser_from_environment(self):
		password = 'Strong-unique-admin-password-8492!'
		with patch.dict(os.environ, {
			'ADMIN_USERNAME': 'aryan',
			'ADMIN_EMAIL': 'aryan@example.com',
			'ADMIN_PASSWORD': password,
		}):
			call_command('bootstrap_admin')

		admin = get_user_model().objects.get(username='aryan')
		self.assertTrue(admin.is_staff)
		self.assertTrue(admin.is_superuser)
		self.assertTrue(admin.check_password(password))

	def test_bootstrap_admin_does_not_change_existing_superuser(self):
		User = get_user_model()
		admin = User.objects.create_superuser(
			username='aryan',
			email='aryan@example.com',
			password='Original-strong-password-8492!',
		)
		with patch.dict(os.environ, {
			'ADMIN_USERNAME': 'aryan',
			'ADMIN_EMAIL': 'aryan@example.com',
			'ADMIN_PASSWORD': 'Another-strong-password-1948!',
		}):
			call_command('bootstrap_admin')

		admin.refresh_from_db()
		self.assertTrue(admin.check_password('Original-strong-password-8492!'))

	def test_bootstrap_admin_resets_existing_superuser_only_when_requested(self):
		User = get_user_model()
		admin = User.objects.create_superuser(
			username='aryan',
			email='aryan@example.com',
			password='Original-strong-password-8492!',
		)
		new_password = 'Replacement-strong-password-3847!'
		with patch.dict(os.environ, {
			'ADMIN_USERNAME': 'aryan',
			'ADMIN_EMAIL': 'aryan@example.com',
			'ADMIN_PASSWORD': new_password,
			'ADMIN_RESET_PASSWORD': 'true',
		}):
			call_command('bootstrap_admin')

		admin.refresh_from_db()
		self.assertTrue(admin.check_password(new_password))

	def test_bootstrap_admin_refuses_to_promote_existing_regular_user(self):
		User = get_user_model()
		User.objects.create_user(
			username='aryan',
			email='aryan@example.com',
			password='Regular-user-password-4829!',
		)
		with patch.dict(os.environ, {
			'ADMIN_USERNAME': 'aryan',
			'ADMIN_EMAIL': 'aryan@example.com',
			'ADMIN_PASSWORD': 'Strong-unique-admin-password-8492!',
		}):
			with self.assertRaises(CommandError):
				call_command('bootstrap_admin')

	def test_signup_reports_duplicate_username(self):
		User = get_user_model()
		User.objects.create_user(
			username='sample-owner',
			email='existing@example.com',
			password='N0t-a-common-password!',
		)

		response = self.client.post('/accounts/signup/', {
			'username': 'SAMPLE-OWNER',
			'email': 'new@example.com',
			'password1': 'N0t-a-common-password!',
			'password2': 'N0t-a-common-password!',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(
			response,
			'That username is already taken. Please choose another.',
		)
		self.assertEqual(User.objects.count(), 1)

	def test_signup_requires_username_and_creates_account(self):
		response = self.client.post('/accounts/signup/', {
			'username': 'sample-owner',
			'email': 'owner@example.com',
			'password1': 'N0t-a-common-password!',
			'password2': 'N0t-a-common-password!',
		})

		self.assertRedirects(response, '/ai/')
		user = get_user_model().objects.get(email='owner@example.com')
		self.assertEqual(user.username, 'sample-owner')
		self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

	def test_signup_logout_and_login_with_email(self):
		password = 'N0t-a-common-password!'
		signup_response = self.client.post('/accounts/signup/', {
			'username': 'sample-owner',
			'email': 'owner@example.com',
			'password1': password,
			'password2': password,
		})
		self.assertRedirects(signup_response, '/ai/')

		user = get_user_model().objects.get(email='owner@example.com')
		self.assertTrue(user.check_password(password))
		logout_response = self.client.post('/accounts/logout/')
		self.assertRedirects(logout_response, '/')

		login_response = self.client.post('/accounts/login/', {
			'username': user.email,
			'password': password,
		})

		self.assertRedirects(login_response, '/ai/')
		self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

	def test_login_uses_email_instead_of_username(self):
		user = get_user_model().objects.create_user(
			username='sample-owner',
			email='owner@example.com',
			password='N0t-a-common-password!',
		)

		response = self.client.post('/accounts/login/', {
			'username': user.email,
			'password': 'N0t-a-common-password!',
		})

		self.assertRedirects(response, '/ai/')
		self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

	def test_login_rejects_username_when_it_is_not_the_email(self):
		get_user_model().objects.create_user(
			username='sample-owner',
			email='owner@example.com',
			password='N0t-a-common-password!',
		)

		response = self.client.post('/accounts/login/', {
			'username': 'sample-owner',
			'password': 'N0t-a-common-password!',
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.wsgi_request.user.is_authenticated)
