from django.contrib import admin
from .models import Website


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'status', 'visit_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['visit_count', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}

