from django.contrib import admin

from .models import BusinessProfile


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
	list_display = ('business_name', 'business_type', 'city', 'state', 'country', 'owner')
	search_fields = ('business_name', 'owner__username', 'city', 'state')
