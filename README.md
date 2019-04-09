# Django Searchable Encrypted Fields
This package provides two types of model field for Django.
1. A series of **EncryptedField** which can be used by themselves. Contents are transparently encrypted/decrypted with AES 256 encryption.
2. A **SearchField** which can be used in conjunction with an EncryptedField. Values are concatentaed with a `hash_key` and then hashed with SHA256 before storing and so can be searched against.

This is probably best demonstrated by example:

```python
class Person(models.Model):
    _name_data = fields.EncryptedCharField(max_length=50, editable=False)
    name = fields.SearchField(encrypted_data_field="_name_data", hash_key="some-key")
    favorite_number = fields.EncryptedIntegerField()
```
You can then use it like:
```python
Person.objects.create(name="Jo", favorite_number=7)
person = Person.objects.get(name="Jo")
assert person.name == "Jo"
assert person.favorite_number == 7
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
