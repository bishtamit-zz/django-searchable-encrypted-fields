# Django Searchable Encrypted Fields
This package is for you if you would like to encrypt model field data "in app" - ie before it is sent to the database.

**Why another encrypted field package?**

1. We use AES-256 encryption with GCM mode (via the Pycryptodome library).
2. It is easy to generate appropriate encryption keys with `secrets.token_hex(32)` from the standard library.
3. You can make 'exact' search lookups when also using the SearchField.

## Install & Setup
```shell
$ pip install django-searchable-encrypted-fields
```
```python
# in settings.py
INSTALLED_APPS += ["encrypted_fields"]

# A list of hex-encoded 32 byte keys
# You only need one unless/until rotating keys
FIELD_ENCRYPTION_KEYS = [
    "f164ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b"
]
```

## Intro
This package provides two types of model field for Django.
1. A series of **EncryptedField** classes which can be used by themselves and work just like their regular Django counterparts. Contents are transparently encrypted/decrypted.
2. A **SearchField** which can be used in conjunction with any EncryptedField. Values are concatentaed with a `hash_key` and then hashed with SHA256 before storing in a separate field. This means 'exact' searches can be performed.

This is probably best demonstrated by example:

## Using a stand-alone EncryptedField
```python
from encrypted_fields import fields

class Person(models.Model):
    favorite_number = fields.EncryptedIntegerField(help_text="Your favorite number.")
```
You can use all the usual field arguments and add validators as normal.
Note, however, that primary_key, unique and db_index are not supported because they do not make sense for encrypted data.


## Using a SearchField along with an EncryptedField
```python
class Person(models.Model):
    _name_data = fields.EncryptedCharField(max_length=50, editable=False)
    name = fields.SearchField(hash_key="f164ec6bd...7ae0d794a9a0b", encrypted_field_name="_name_data", )
    favorite_number = fields.EncryptedIntegerField()
    city = models.CharField(max_length=255) # regular Django model field
```
You can then use it like:
```python
# "Jo" is hashed and stored in 'name' as well as symmetrically encrypted and stored in '_name_data'
Person.objects.create(name="Jo", favorite_number=7, city="London")
person = Person.objects.get(name="Jo")
assert person.name == "Jo"
assert person.favorite_number == 7

person = Person.objects.get(city="London")
assert person.name == "Jo" . # the data is taken from '_name_data', which decrypts it first.
```
You can safely update like this:
```python
person.name = "Simon"
person.save()
```
But when using `update()` you need to provide the value to both fields:
```python
Person.objects.filter(name="Jo").update(name="Bob", _name_data="Bob")
```
A SearchField inherits the validators and formfield (widget) from its associated EncryptedField. So:

1. Do not add validators or form widgets to SearchFields (they will be ignored), add them to the associated EncryptedField instead.
2. Do not include the EncryptedField in forms, instead just display the SearchField.

**Note** Although unique validation (and unique constraints at the database level) for an EncryptedField makes little sense, it is possible to add `unique=True` to a SearchField.

An example of when this makes sense is in a custom user model, where the `username` field is replaced with an `EncryptedCharField` and `SearchField`. Please see the custom user model in `encrypted_fields_test.models` and its tests for an example.

## Included EncryptedField classes
The following are included:
```python
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
```
Note that, although untested, you should be able to extend other regular Django model field classes like this:
```python
class EncryptedIPAddressField(EncryptedFieldMixin, models.GenericIPAddressField):
    pass
```
Please let us know if you have problems when doing this.
## Generating Encryption Keys
You can use `secrets` from the standard library. It will print appropriate hex-encoded keys to the terminal, ready to be used in `settings.FIELD_ENCRYPTION_KEYS` or as a hash_key for a SearchField:
```shell
$ python manage.py shell
>>> import secrets
>>> secrets.token_hex(32)
```
Note: Thanks to Andrew Mendoza for the suggestion.

Note: encryption keys **must** be hex encoded and 32 bytes

**Important**: use different hash_key values for each SearchField and make sure they are different from any keys in `settings.FIELD_ENCRYPTION_KEYS`.
## Rotating Encryption Keys
If you want to rotate the encryption key just prepend `settings.FIELD_ENCRYPTION_KEYS` with a new key. This new key (the first in the list) will be used for encrypting/decrypting all data. If decrypting data fails (because it was encrypted with an older key), each key in the list is tried.
## Compatability
`django-searchable-encrypted-fields` is tested with Django(2.1, 2.2, 3.0, 3.1) on Python(3.6, 3.7, 3.8) using SQLite and PostgreSQL (10 and 11).

Test coverage is at 96%.
