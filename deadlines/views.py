from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from documents.models import Document


@login_required
def deadline_list(request):
	today = timezone.localdate()
	owned_expiring_documents = Document.objects.filter(
		owner=request.user,
		expiry_date__isnull=False,
	).select_related('requirement')
	action_documents = owned_expiring_documents.filter(expiry_date__lte=today).order_by('expiry_date', 'title')
	expiring_documents = owned_expiring_documents.filter(
		expiry_date__gt=today,
		expiry_date__lte=today + timedelta(days=10),
	).order_by('expiry_date', 'title')
	return render(request, 'deadlines/list.html', {
		'action_documents': action_documents,
		'expiring_documents': expiring_documents,
		'today': today,
	})
