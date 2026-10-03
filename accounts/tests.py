from django.test import TestCase
from django.contrib.auth import get_user_model


class AccountFlowTests(TestCase):
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
