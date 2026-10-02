from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from businesses.models import BusinessProfile

from .models import RequirementApplication
from .services import matching_requirements


@login_required
@require_http_methods(['GET', 'POST'])
def requirement_detail(request, requirement_id):
	profile = BusinessProfile.objects.filter(owner=request.user).first()
	if profile is None:
		return redirect('ai_assistant')

	requirement = get_object_or_404(matching_requirements(profile), pk=requirement_id)
	application = RequirementApplication.objects.filter(
		owner=request.user,
		requirement=requirement,
	).first()

	if request.method == 'POST':
		if application is None:
			application = RequirementApplication.objects.create(
				owner=request.user,
				requirement=requirement,
				status=RequirementApplication.Status.APPLIED,
				applied_at=timezone.now(),
			)
		elif application.status != RequirementApplication.Status.DOCUMENT_UPLOADED:
			application.status = RequirementApplication.Status.APPLIED
			application.applied_at = timezone.now()
			application.save(update_fields=['status', 'applied_at', 'updated_at'])
		messages.success(request, 'Application marked as submitted. Upload the document you received.')
		return redirect('documents:upload_for_requirement', requirement_id=requirement.pk)

	return render(request, 'compliance/requirement_detail.html', {
		'requirement': requirement,
		'application': application,
	})
