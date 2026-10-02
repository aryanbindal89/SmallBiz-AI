from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('ai/', include('ai_assistant.urls')),
    path('compliance/', include('compliance.urls')),
    path('documents/', include('documents.urls')),
    path('deadlines/', include('deadlines.urls')),
    path('admin/', admin.site.urls),
]
