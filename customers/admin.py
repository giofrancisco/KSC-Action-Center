from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "ksc_host", "ksc_port", "active", "updated_at")
    list_filter = ("active",)
    search_fields = ("name", "code", "ksc_host")
