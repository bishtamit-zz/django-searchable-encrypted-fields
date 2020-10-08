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
        "info",
        "created_at",
        "updated_at",
        "default_char",
        "_default_char_data",
        "default_number",
        "_default_number_data",
        "default_date",
        "_default_date_data",
    )
    readonly_fields = (
        "_name_data",
        "_number_data",
        "_email_data",
        "_date_data",
        "_text_data",
        "created_at",
        "updated_at",
        "_default_char_data",
        "_default_number_data",
        "_default_date_data",
    )

    search_fields = (
        "email__exact",
        "name__exact",
        "date__exact",
        "number__exact",
        "text__exact",
    )


@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    pass
