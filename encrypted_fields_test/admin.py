from django.contrib import admin
from django.conf import settings

from .models import DemoModel

admin.AdminSite.site_header = "Field Test Admin"


@admin.register(DemoModel)
class DemoModelAdmin(admin.ModelAdmin):
    fields = (
        "email",
        "_email_data",
        "name",
        "_name_data",
        "number",
        "_number_data",
        "date",
        "_date_data",
        "date_2",
    )
    readonly_fields = ("_name_data", "_number_data", "_email_data", "_date_data")

    search_fields = ("email__exact", "name__exact", "date__exact", "number__exact")
