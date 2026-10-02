from django.conf import settings
from django.db import models
from django.utils import timezone


class Deadline(models.Model):
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deadlines')
	title = models.CharField(max_length=160)
	details = models.CharField(max_length=300, blank=True)
	due_date = models.DateField()
	is_complete = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['due_date', 'title']

	def __str__(self):
		return self.title

	@property
	def days_until_due(self):
		return (self.due_date - timezone.localdate()).days

	@property
	def alert_state(self):
		if self.is_complete:
			return 'complete'
		if self.days_until_due < 0:
			return 'overdue'
		if self.days_until_due == 0:
			return 'today'
		if self.days_until_due <= 7:
			return 'soon'
		return 'upcoming'

	@property
	def alert_label(self):
		if self.alert_state == 'soon':
			unit = 'day' if self.days_until_due == 1 else 'days'
			return f'Due in {self.days_until_due} {unit}'
		if self.alert_state == 'overdue':
			overdue_days = abs(self.days_until_due)
			unit = 'day' if overdue_days == 1 else 'days'
			return f'{overdue_days} {unit} overdue'
		return {
			'complete': 'Complete',
			'today': 'Due today',
			'upcoming': f"Due {self.due_date.strftime('%b %d').replace(' 0', ' ')}",
		}[self.alert_state]
