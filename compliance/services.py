from django.db.models import Q

from .models import ComplianceRequirement


def matching_requirements(profile):
    requirements = ComplianceRequirement.objects.filter(is_active=True)

    for field in ('business_type', 'country', 'state', 'city'):
        value = getattr(profile, field)
        requirements = requirements.filter(
            Q(**{field: ''}) | Q(**{f'{field}__iexact': value})
        )

    if profile.employee_count is None:
        requirements = requirements.filter(
            minimum_employees__isnull=True,
            maximum_employees__isnull=True,
        )
    else:
        requirements = requirements.filter(
            Q(minimum_employees__isnull=True) |
            Q(minimum_employees__lte=profile.employee_count),
        ).filter(
            Q(maximum_employees__isnull=True) |
            Q(maximum_employees__gte=profile.employee_count),
        )

    return requirements.order_by('name')