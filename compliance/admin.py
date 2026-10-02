from django.contrib import admin

from .models import ComplianceRequirement, RequirementApplication


@admin.register(ComplianceRequirement)
class ComplianceRequirementAdmin(admin.ModelAdmin):
	list_display = ('name', 'business_type', 'country', 'state', 'city', 'is_active', 'updated_at')
	list_filter = ('is_active', 'business_type', 'country', 'state')
	search_fields = ('name', 'summary', 'country', 'state', 'city')


@admin.register(RequirementApplication)
class RequirementApplicationAdmin(admin.ModelAdmin):
	list_display = ('requirement', 'owner', 'status', 'applied_at', 'updated_at')
	list_filter = ('status',)
	search_fields = ('requirement__name', 'owner__username')
