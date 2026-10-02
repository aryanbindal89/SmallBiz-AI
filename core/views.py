from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from deadlines.models import Deadline
from documents.models import Document


def home(request):
    if request.user.is_authenticated:
        return redirect('ai_assistant')
    return render(request, 'home.html')


@login_required(login_url='/accounts/login/')
def dashboard(request):
    today = timezone.localdate()
    open_deadlines = Deadline.objects.filter(owner=request.user, is_complete=False)
    documents = Document.objects.filter(owner=request.user)
    stats = [
        {'label': 'Open deadlines', 'value': open_deadlines.count(), 'note': 'Need tracking'},
        {'label': 'Due soon or overdue', 'value': open_deadlines.filter(due_date__lte=today + timedelta(days=7)).count(), 'note': 'Review these alerts'},
        {'label': 'Documents', 'value': documents.count(), 'note': 'Private uploads'},
    ]
    alerts = open_deadlines.filter(due_date__lte=today + timedelta(days=30))[:5]

    return render(request, 'dashboard.html', {
        'stats': stats,
        'alerts': alerts,
        'documents': documents[:5],
    })
