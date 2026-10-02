from django.urls import path

from . import views

app_name = 'compliance'

urlpatterns = [
    path('requirements/<int:requirement_id>/', views.requirement_detail, name='requirement_detail'),
]