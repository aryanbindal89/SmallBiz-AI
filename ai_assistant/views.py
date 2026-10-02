from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from businesses.forms import BusinessProfileForm
from businesses.models import BusinessProfile
from compliance.models import RequirementApplication
from compliance.services import matching_requirements

from .formatting import parse_assistant_response
from .services import explain_business_requirement


@login_required(login_url='/accounts/login/')
def ai_assistant(request):
    profile = BusinessProfile.objects.filter(owner=request.user).first()
    profile_data = request.POST if request.method == 'POST' and request.POST.get('action') == 'save_profile' else None
    profile_form = BusinessProfileForm(profile_data, instance=profile)
    result = None
    error = None
    response_sections = []
    response_keywords = []

    if request.method == 'POST' and request.POST.get('action') == 'save_profile':
        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.owner = request.user
            profile.save()
            messages.success(request, 'Business profile saved. Matching requirements are below.')
            return redirect('ai_assistant')
    elif request.method == 'POST':
        question = (request.POST.get('question') or '').strip()
        business_context = request.POST.get('business_context', '').strip()

        if profile is None:
            error = 'Add your business information before asking a compliance question.'
        elif not question:
            error = 'Please enter a compliance question.'
        else:
            if not business_context:
                business_context = ', '.join(filter(None, [
                    profile.business_name,
                    profile.business_activity,
                    profile.get_business_type_display(),
                    profile.city,
                    profile.state,
                    profile.country,
                    f'{profile.employee_count} employees' if profile.employee_count is not None else '',
                ]))
            try:
                result = explain_business_requirement(question, business_context)
                response_sections, response_keywords = parse_assistant_response(result)
            except ValueError as exc:
                error = str(exc)
            except Exception:  # pragma: no cover - external API fallback
                error = 'The assistant is temporarily unavailable. Please try again in a moment.'

    requirement_records = []
    if profile is not None:
        applications = {
            application.requirement_id: application
            for application in RequirementApplication.objects.filter(owner=request.user)
        }
        requirement_records = [
            {'requirement': requirement, 'application': applications.get(requirement.pk)}
            for requirement in matching_requirements(profile)
        ]
    portal_records = [
        record for record in requirement_records
        if record['requirement'].official_portal_url
    ]

    return render(request, 'ai_assistant.html', {
        'profile': profile,
        'profile_form': profile_form,
        'requirement_records': requirement_records,
        'portal_records': portal_records,
        'result': result,
        'error': error,
        'response_sections': response_sections,
        'response_keywords': response_keywords,
        'question': request.POST.get('question', '') if request.method == 'POST' else '',
        'business_context': request.POST.get('business_context', '') if request.method == 'POST' else '',
    })
