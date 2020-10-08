import hashlib
import string
from inspect import isclass

from Crypto.Cipher import AES
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    AdminEmailInputWidget,
    AdminDateWidget,
    AdminIntegerFieldWidget,
    AdminBigIntegerFieldWidget,
    AdminSplitDateTime,
    AdminTextareaWidget,
)


__all__ = [
    "EncryptedFieldMixin",
    "EncryptedTextField",
    "EncryptedCharField",
    "EncryptedEmailField",
    "EncryptedIntegerField",
    "EncryptedDateField",
    "EncryptedDateTimeField",
    "EncryptedBigIntegerField",
    "EncryptedPositiveIntegerField",
    "EncryptedPositiveSmallIntegerField",
    "EncryptedSmallIntegerField",
    "SearchField",
]


class EncryptedFieldMixin(models.Field):
    """A field that encrypts values with AES 256 symmetric encryption,
    using Pycryptodome.

    Note: Be careful not to change/alter a pre-existing regular django field to be an
    EncryptedField. The data for existing rows will be unencrypted in the database and
    appear 'corrupted' when trying to decrypt/fetch it.
    Instead, add the new EncryptedField to the model and do a data-migration
    to transfer data from the old field.
    """

    def __init__(self, *args, **kwargs):
        if kwargs.get("primary_key"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not support primary_key=True."
            )
        if kwargs.get("unique"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not support unique=True."
            )
        if kwargs.get("db_index"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not support db_index=True."
            )
        self._internal_type = "BinaryField"
        super().__init__(*args, **kwargs)

    @cached_property
    def keys(self):
        # should be a list or tuple of hex encoded 32byte keys
        key_list = settings.FIELD_ENCRYPTION_KEYS
        if not isinstance(key_list, (list, tuple)):
            raise ImproperlyConfigured("FIELD_ENCRYPTION_KEYS should be a list.")
        return key_list

    def encrypt(self, data_to_encrypt):
        if not isinstance(data_to_encrypt, str):
            data_to_encrypt = str(data_to_encrypt)
        cipher = AES.new(bytes.fromhex(self.keys[0]), AES.MODE_GCM)
        nonce = cipher.nonce
        cypher_text, tag = cipher.encrypt_and_digest(data_to_encrypt.encode())
        return nonce + tag + cypher_text

    def decrypt(self, value):
        nonce = value[:16]
        # Perform same nonce checks here as Pycryptodome, so we can raise a more user
        # friendly error message
        if not isinstance(nonce, (bytes, bytearray, memoryview)) or len(nonce) != 16:
            raise ValueError("Data is corrupted.")
        tag = value[16:32]
        cypher_text = value[32:]
        counter = 0
        num_keys = len(self.keys)
        while counter < num_keys:
            cipher = AES.new(
                bytes.fromhex(self.keys[counter]), AES.MODE_GCM, nonce=nonce
            )
            try:
                plaintext = cipher.decrypt_and_verify(cypher_text, tag)
            except ValueError:
                counter += 1
                continue
            return plaintext.decode()
        raise ValueError("AES Key incorrect or data is corrupted")

    def get_internal_type(self):
        return self._internal_type

    def get_db_prep_save(self, value, connection):
        if self.empty_strings_allowed and value == bytes():
            # This tackles a corner case effecting string-based (eg Char/Text) fields
            # during migrations when null=False, blank=True and no default has been declared.
            # Because we are a BinaryField, a value of bytes() is provided instead of str().
            # See https://github.com/django/django/blob/2.2.16/django/db/backends/base/schema.py#L215
            # We change this to "" to prevent str(bytes()), ie a literal "b''" being
            # used as the default to populate pre-existing records.
            value = ""
        value = super().get_db_prep_save(value, connection)
        if value is not None:
            encrypted_value = self.encrypt(value)
            return connection.Database.Binary(encrypted_value)

    def from_db_value(self, value, expression, connection):
        if value is not None:
            return self.to_python(self.decrypt(value))

    @cached_property
    def validators(self):
        # For IntegerField (and subclasses) we must pretend to be that
        # field type to get proper validators.
        self._internal_type = super().get_internal_type()
        try:
            return super().validators
        finally:
            self._internal_type = "BinaryField"


class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    pass


class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    pass


class EncryptedEmailField(EncryptedFieldMixin, models.EmailField):
    pass


class EncryptedIntegerField(EncryptedFieldMixin, models.IntegerField):
    pass


class EncryptedPositiveIntegerField(EncryptedFieldMixin, models.PositiveIntegerField):
    pass


class EncryptedPositiveSmallIntegerField(
    EncryptedFieldMixin, models.PositiveSmallIntegerField
):
    pass


class EncryptedSmallIntegerField(EncryptedFieldMixin, models.SmallIntegerField):
    pass


class EncryptedBigIntegerField(EncryptedFieldMixin, models.BigIntegerField):
    pass


class EncryptedDateField(EncryptedFieldMixin, models.DateField):
    pass


class EncryptedDateTimeField(EncryptedFieldMixin, models.DateTimeField):
    pass


SEARCH_HASH_PREFIX = "xx"


def is_hashed_already(data_string):
    # return True if the SearchField has hashed this data before
    # we have SEARCH_HASH_PREFIX to make sure we can distinguish our hashing
    # from raw data that looks like a hash, eg: a txid or perhaps a payment_id
    if data_string is None:
        return False

    if not isinstance(data_string, str):
        return False

    if not data_string.startswith(SEARCH_HASH_PREFIX):
        return False

    actual_hash = data_string[len(SEARCH_HASH_PREFIX) :]

    if len(actual_hash) != 64:
        return False

    return all([char in string.hexdigits for char in actual_hash])


class SearchFieldDescriptor:
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.field.encrypted_field_name in instance.__dict__:
            decrypted_data = instance.__dict__[self.field.encrypted_field_name]
        else:
            instance.refresh_from_db(fields=[self.field.encrypted_field_name])
            decrypted_data = getattr(instance, self.field.encrypted_field_name)

        # swap data from encrypted_field to search_field
        setattr(instance, self.field.name, decrypted_data)

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
        if not is_hashed_already(value):
            # if the value has been hashed already, don't pass the value to encrypted_field.
            # otherwise will overwrite the real data with an encrypted version of the hash!!
            instance.__dict__[self.field.encrypted_field_name] = value


class SearchField(models.CharField):
    """
    A Search field to accompany an Encrypted Field. A keyed hash of the value is stored and searched against.

    The user provided hash_key should be suitably long and random to prevent being able to 'guess' the value
    The user must provide an encrypted_field_name of the corresponding encrypted-data field in the same model.

    Notes:
         Do not use model.objects.update() unless you update both the SearchField and the associated EncryptedField.
         Always add a SearchField to a model, don't change/alter an existing regular django field.

    Note on Defaults:
        To make sure the expected 'default=' value is used (in both SearchField and EncryptedField),
        the SearchField must always use the EncryptedField's 'default=' value.
        This ensures the correct default is used in both fields for:
        1. Initial values in forms
        2. Migrations (adding defaults to existing rows)
        3. Saving model instances
        Having different defaults on the SearchField and Encrypted field, eg only setting
        default on one of them, leads to some unexpected and strange behaviour.
    """

    description = "A secure SearchField to accompany an EncryptedField"
    descriptor_class = SearchFieldDescriptor

    def __init__(self, hash_key=None, encrypted_field_name=None, *args, **kwargs):
        if hash_key is None:
            raise ImproperlyConfigured("you must supply a hash_key")
        self.hash_key = hash_key

        if encrypted_field_name is None:
            raise ImproperlyConfigured(
                "you must supply the name of the accompanying Encrypted Field"
                " that will hold the data"
            )
        if not isinstance(encrypted_field_name, str):
            raise ImproperlyConfigured("'encrypted_field_name' must be a string")
        self.encrypted_field_name = encrypted_field_name

        if kwargs.get("primary_key"):
            raise ImproperlyConfigured("SearchField does not support primary_key=True.")
        if "default" in kwargs:
            # We always use EncryptedField's default.
            raise ImproperlyConfigured(
                f"SearchField does not support 'default='. Set 'default=' on '{self.encrypted_field_name}' instead"
            )
        if "db_index" not in kwargs:
            # if not specified we should index by default.
            kwargs["db_index"] = True  # it is a field for searching!
        kwargs["max_length"] = 64 + len(SEARCH_HASH_PREFIX)  # will be sha256 hex digest
        kwargs["null"] = True  # should be nullable, in case data field is nullable.
        kwargs[
            "blank"
        ] = True  # to be consistent with 'null'. Forms are not based on SearchField anyway.
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Only include kwarg if it's not the default (None)
        if self.hash_key:
            kwargs["hash_key"] = self.hash_key
        if self.encrypted_field_name:
            kwargs["encrypted_field_name"] = self.encrypted_field_name
        return name, path, args, kwargs

    def has_default(self):
        """Always use the EncryptedFields default"""
        return self.model._meta.get_field(self.encrypted_field_name).has_default()

    def get_default(self):
        """Always use EncryptedField's default."""
        return self.model._meta.get_field(self.encrypted_field_name).get_default()

    def get_prep_value(self, value):
        if value is None:
            return value
        # coerce to str before encoding and hashing

        # NOTE: not sure what happens when the str format for date/datetime is changed??
        # Should not matter as we are dealing with a datetime object in this case.
        # Eg str(datetime(10, 9, 2020))
        value = str(value)

        if is_hashed_already(value):
            # if we have hashed this previously, don't do it again
            return value

        v = value + self.hash_key
        return SEARCH_HASH_PREFIX + hashlib.sha256(v.encode()).hexdigest()

    def formfield(self, **kwargs):
        """Use formfield from self.encrypted_field_name, passing kwargs along
        (eg custom widget/help_text/label kwargs).

        if 'label' is not in kwargs then add this field's 'verbose_name' as 'label',
        otherwise the default 'verbose_name' of the encrypted field will be used in
        the widget.

        If called by Admin Panel, with the default widget ('AdminTextInputWidget'),
        in kwargs, then change to appropriate default admin widget for the encrypted
        field class.
        """
        defaults = {}
        if kwargs.get("label") is None:
            defaults.update({"label": capfirst(self.verbose_name)})
        widget = kwargs.get("widget")
        if isclass(widget) and issubclass(widget, AdminTextInputWidget):
            # is Admin Panel and we should change to appropriate widget.
            encrypted_field = self.model._meta.get_field(self.encrypted_field_name)
            if isinstance(encrypted_field, EncryptedEmailField):
                defaults.update({"widget": AdminEmailInputWidget})
            elif isinstance(encrypted_field, EncryptedDateField):
                defaults.update({"widget": AdminDateWidget})
            elif isinstance(encrypted_field, EncryptedDateTimeField):
                defaults.update({"widget": AdminSplitDateTime})
            elif isinstance(encrypted_field, EncryptedIntegerField):
                defaults.update({"widget": AdminIntegerFieldWidget})
            elif isinstance(encrypted_field, EncryptedPositiveIntegerField):
                defaults.update({"widget": AdminIntegerFieldWidget})
            elif isinstance(encrypted_field, EncryptedPositiveSmallIntegerField):
                defaults.update({"widget": AdminIntegerFieldWidget})
            elif isinstance(encrypted_field, EncryptedSmallIntegerField):
                defaults.update({"widget": AdminIntegerFieldWidget})
            elif isinstance(encrypted_field, EncryptedBigIntegerField):
                defaults.update({"widget": AdminBigIntegerFieldWidget})
            elif isinstance(encrypted_field, EncryptedTextField):
                defaults.update({"widget": AdminTextareaWidget})
        kwargs.update(defaults)
        return self.model._meta.get_field(self.encrypted_field_name).formfield(**kwargs)

    def clean(self, value, model_instance):
        """Validate value against the validators from self.encrypted_field_name.
        Any validators on SearchField will be ignored.

        SearchField's 'max_length' constraint will still be enforced at the database
        level, but applied to the saved hash value."""
        return model_instance._meta.get_field(self.encrypted_field_name).clean(
            value, model_instance
        )

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self.descriptor_class(self))


def get_prep_lookup_error(self):
    """Raise errors for unsupported lookups"""
    raise FieldError(
        f"{self.lhs.field.__class__.__name__} does not support '{self.lookup_name}' lookups"
    )


for name, lookup in models.Field.class_lookups.items():
    """Register inappropriate lookups with our error handler.
    We allow 'isnull' for EncryptedField and 'isnull' and 'exact' for SearchField."""
    # Dynamically create classes that inherit from the right lookups
    if name != "isnull":
        lookup_class = type(
            "EncryptedField" + name,
            (lookup,),
            {"get_prep_lookup": get_prep_lookup_error},
        )
        EncryptedFieldMixin.register_lookup(lookup_class)
    if name not in ["isnull", "exact"]:
        lookup_class = type(
            "SearchField" + name, (lookup,), {"get_prep_lookup": get_prep_lookup_error}
        )
        SearchField.register_lookup(lookup_class)
