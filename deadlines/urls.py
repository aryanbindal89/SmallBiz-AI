from django.urls import path

from . import views

app_name = 'deadlines'

urlpatterns = [
    path('', views.deadline_list, name='list'),
]