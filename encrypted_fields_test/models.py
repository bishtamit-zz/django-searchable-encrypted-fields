import datetime
from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.urls import reverse
from encrypted_fields import fields


class EncryptedText(models.Model):
    value = fields.EncryptedTextField()


class EncryptedChar(models.Model):
    value = fields.EncryptedCharField(max_length=25)


class EncryptedEmail(models.Model):
    value = fields.EncryptedEmailField()


class EncryptedInt(models.Model):
    value = fields.EncryptedIntegerField()


class EncryptedDate(models.Model):
    value = fields.EncryptedDateField()


class EncryptedDateTime(models.Model):
    value = fields.EncryptedDateTimeField()


class EncryptedNullable(models.Model):
    value = fields.EncryptedIntegerField(null=True)


class SearchText(models.Model):
    value = fields.EncryptedTextField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchChar(models.Model):
    value = fields.EncryptedCharField(max_length=25)
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchEmail(models.Model):
    value = fields.EncryptedEmailField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchInt(models.Model):
    value = fields.EncryptedIntegerField(validators=[validators.MaxValueValidator(10)])
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchBigInt(models.Model):
    value = fields.EncryptedBigIntegerField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchSmallInt(models.Model):
    value = fields.EncryptedSmallIntegerField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchPosSmallInt(models.Model):
    value = fields.EncryptedPositiveSmallIntegerField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchPosInt(models.Model):
    value = fields.EncryptedPositiveIntegerField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchDate(models.Model):
    value = fields.EncryptedDateField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchDateTime(models.Model):
    value = fields.EncryptedDateTimeField()
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchCharWithDefault(models.Model):
    value = fields.EncryptedCharField(max_length=25, default="foo")
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchDateWithDefault(models.Model):
    value = fields.EncryptedDateField(default=datetime.date.today)
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class SearchIntWithDefault(models.Model):
    value = fields.EncryptedIntegerField(
        validators=[validators.MaxValueValidator(10)], default=2
    )
    search = fields.SearchField(hash_key="abc123", encrypted_field_name="value")


class DemoModel(models.Model):
    """Note that all regulare kwargs are added to EncryptedFields and not SearchFields.
    Eg 'default=', 'null=', 'blank='.

    Also note that we declare the SearchField *after* its EncryptedField. This is only
    important when using DRF ModelSerializers, but never the less should be the standard
    way of doing it."""

    _email_data = fields.EncryptedEmailField()
    email = fields.SearchField(hash_key="123abc", encrypted_field_name="_email_data")
    _name_data = fields.EncryptedCharField(
        max_length=10, blank=True, null=True, help_text="This field is not required."
    )
    name = fields.SearchField(hash_key="123abc", encrypted_field_name="_name_data")
    _date_data = fields.EncryptedDateField()
    date = fields.SearchField(hash_key="123abc", encrypted_field_name="_date_data")
    date_2 = fields.EncryptedDateField(
        blank=True,
        null=True,
        help_text="This field is just encrypted and is not required.",
    )
    _number_data = fields.EncryptedPositiveSmallIntegerField()
    number = fields.SearchField(hash_key="123abc", encrypted_field_name="_number_data")
    _text_data = fields.EncryptedTextField(
        help_text="A text area. Not typically used with a SearchField."
    )
    text = fields.SearchField(hash_key="123abc", encrypted_field_name="_text_data")
    info = fields.EncryptedCharField(
        blank=True,
        null=False,
        max_length=20,
        help_text="Char field, required at db level, without a default and blank=True",
    )
    # Examples with defaults
    _default_date_data = fields.EncryptedDateField(default=datetime.date.today)
    default_date = fields.SearchField(
        hash_key="123abc", encrypted_field_name="_default_date_data"
    )
    _default_number_data = fields.EncryptedPositiveSmallIntegerField(default=1)
    default_number = fields.SearchField(
        hash_key="123abc", encrypted_field_name="_default_number_data"
    )
    _default_char_data = fields.EncryptedCharField(default="foo default", max_length=20)
    default_char = fields.SearchField(
        hash_key="123abc", encrypted_field_name="_default_char_data"
    )

    # typical use case
    created_at = fields.EncryptedDateTimeField(auto_now_add=True)
    updated_at = fields.EncryptedDateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pk}: {self.name}"

    def get_absolute_url(self):
        return reverse("demomodel-list")


class DemoMigrationModel(models.Model):
    """A model to demonstrate and test migrations from a regular django field to an
    EncryptedField, regular django field to a SearchField and also an EncryptedField to
    a SearchField.

    See the 'migrations' directory and tests."""

    data = models.CharField(max_length=10, default="hi")
    info = models.CharField(max_length=10, default="")
    # Used to demo migrating 'data' to an EncryptedField
    encrypted_data = fields.EncryptedCharField(max_length=20, default="hi")
    # Used to demo migrating 'info' to a SearchField (with associated EncryptedField):
    encrypted_info = fields.EncryptedCharField(max_length=20, default="")
    searchable_encrypted_info = fields.SearchField(
        hash_key="abc", encrypted_field_name="encrypted_info"
    )
    # Used to demo migrating 'encrypted_data' to a SearchField:
    _encrypted_data = fields.EncryptedCharField(max_length=20, default="hi")
    searchable_encrypted_data = fields.SearchField(
        hash_key="abcd", encrypted_field_name="_encrypted_data"
    )
    # New fields with defaults added 'later' in a different migration.
    _default_date = fields.EncryptedDateField(default=datetime.date.today)
    searchable_default_date = fields.SearchField(
        hash_key="123abc", encrypted_field_name="_default_date"
    )
    _default_number = fields.EncryptedPositiveSmallIntegerField(default=1)
    searchable_default_number = fields.SearchField(
        hash_key="123abc", encrypted_field_name="_default_number"
    )
    _default_char = fields.EncryptedCharField(default="foo default", max_length=20)
    searchable_default_char = fields.SearchField(
        hash_key="123abc", encrypted_field_name="_default_char"
    )
    default_encrypted_char = fields.EncryptedCharField(
        max_length=20, default="encrypted hi"
    )

    def __str__(self):
        return self.info


class User(AbstractUser):
    """Example of replacing 'username' with Search and Encryption fields.

    Note we add the unique constraint to the SearchField."""

    username_validator = UnicodeUsernameValidator()
    _username = fields.EncryptedCharField(
        max_length=150,
        validators=[username_validator],
    )
    username = fields.SearchField(
        hash_key="abc123",
        encrypted_field_name="_username",
        unique=True,
        error_messages={
            "unique": "Custom error message for already exists.",
        },
    )
    USERNAME_FIELD = "username"
