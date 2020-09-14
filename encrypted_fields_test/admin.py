from django.contrib import admin
from django.conf import settings

from .models import DemoModel, User

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
        "text",
        "_text_data",
    )
    readonly_fields = (
        "_name_data",
        "_number_data",
        "_email_data",
        "_date_data",
        "_text_data",
    )

    search_fields = ("email__exact", "name__exact", "date__exact", "number__exact")


@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    pass
