from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import EmailAuthenticationForm, SignUpForm


class LoginView(auth_views.LoginView):
	template_name = 'registration/login.html'
	authentication_form = EmailAuthenticationForm


class SignUpView(FormView):
	template_name = 'registration/signup.html'
	form_class = SignUpForm
	success_url = reverse_lazy('ai_assistant')

	def form_valid(self, form):
		user = form.save()
		login(self.request, user, backend='accounts.backends.EmailBackend')
		messages.success(self.request, 'Your account is ready.')
		return super().form_valid(form)
