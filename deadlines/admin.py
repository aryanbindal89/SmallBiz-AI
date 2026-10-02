from django.contrib import admin

from .models import Deadline


@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
	list_display = ('title', 'owner', 'due_date', 'is_complete')
	list_filter = ('is_complete', 'due_date')
	search_fields = ('title', 'owner__username')
