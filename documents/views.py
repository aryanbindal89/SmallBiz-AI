from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from compliance.models import RequirementApplication

from .forms import DocumentUpdateForm, DocumentUploadForm
from .models import Document


def _mark_requirement_document_uploaded(document):
	if document.requirement_id is None:
		return
	application = RequirementApplication.objects.filter(
		owner=document.owner,
		requirement=document.requirement,
	).first()
	if application is not None and application.status != RequirementApplication.Status.DOCUMENT_UPLOADED:
		application.status = RequirementApplication.Status.DOCUMENT_UPLOADED
		application.save(update_fields=['status', 'updated_at'])


def _document_list_context(request, form, requirement=None):
	return {
		'form': form,
		'documents': Document.objects.filter(owner=request.user).select_related('requirement'),
		'requirement': requirement,
	}


@login_required
def document_list(request):
	form = DocumentUploadForm(request.POST or None, request.FILES or None, owner=request.user)
	if request.method == 'POST' and form.is_valid():
		document = form.save(commit=False)
		document.owner = request.user
		document.save()
		_mark_requirement_document_uploaded(document)
		messages.success(request, f'{document.title} was uploaded.')
		return redirect('documents:list')

	return render(request, 'documents/list.html', _document_list_context(request, form))


@login_required
def upload_for_requirement(request, requirement_id):
	application = get_object_or_404(
		RequirementApplication.objects.select_related('requirement'),
		owner=request.user,
		requirement_id=requirement_id,
	)
	form = DocumentUploadForm(
		request.POST or None,
		request.FILES or None,
		owner=request.user,
		required_requirement=application.requirement,
	)
	if request.method == 'POST' and form.is_valid():
		document = form.save(commit=False)
		document.owner = request.user
		document.requirement = application.requirement
		document.save()
		_mark_requirement_document_uploaded(document)
		messages.success(request, f'{document.title} was uploaded for {application.requirement.name}.')
		return redirect('documents:list')

	return render(
		request,
		'documents/list.html',
		_document_list_context(request, form, application.requirement),
	)


@login_required
def edit_document(request, document_id):
	document = get_object_or_404(
		Document.objects.select_related('requirement'),
		pk=document_id,
		owner=request.user,
	)
	form = DocumentUpdateForm(request.POST or None, instance=document)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, f'{document.title} details were updated.')
		return redirect('documents:list')
	return render(request, 'documents/edit.html', {'document': document, 'form': form})


@login_required
def download_document(request, document_id):
	document = get_object_or_404(Document, pk=document_id, owner=request.user)
	return FileResponse(
		document.file.open('rb'),
		as_attachment=True,
		filename=Path(document.file.name).name,
	)
