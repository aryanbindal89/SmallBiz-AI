from django.urls import path

from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('requirements/<int:requirement_id>/upload/', views.upload_for_requirement, name='upload_for_requirement'),
    path('<int:document_id>/edit/', views.edit_document, name='edit'),
    path('<int:document_id>/download/', views.download_document, name='download'),
]