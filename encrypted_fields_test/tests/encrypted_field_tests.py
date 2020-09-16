from datetime import date, datetime, timedelta
import os

from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import connection, models as dj_models
from django.utils import timezone
import pytest

from encrypted_fields import fields
from .. import models

DATE1 = date.today()
DATE2 = DATE1 + timedelta(days=2)
DATETIME1 = datetime.utcnow()
if os.environ.get("USE_PG"):  # sqlite is not timezone compatible but postgres is.
    DATETIME1 = timezone.now()
DATETIME2 = DATETIME1 + timedelta(minutes=5)


class TestEncryptedField:
    def test_key_from_settings(self, settings):
        """Use settings.FIELD_ENCRYPTION_KEYS."""
        settings.FIELD_ENCRYPTION_KEYS = ["secret"]
        f = fields.EncryptedTextField()

        assert f.keys == settings.FIELD_ENCRYPTION_KEYS

    def test_key_from_settings_error(self, settings):
        """settings.FIELD_ENCRYPTION_KEYS should be list or tuple."""
        settings.FIELD_ENCRYPTION_KEYS = "secret"
        with pytest.raises(ImproperlyConfigured):
            f = fields.EncryptedTextField()
            f.keys

    def test_key_rotation(self, settings, db):
        """Can supply multiple `keys` for key rotation."""
        settings.FIELD_ENCRYPTION_KEYS = [
            "f164ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
            "e364ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
        ]
        # clear keys cached_property if populated
        field1 = models.EncryptedChar._meta.get_field("value")
        if field1.keys:
            del field1.keys
        keys = field1.keys
        # keys will be re-populated here
        models.EncryptedChar.objects.create(value="hello")
        m1 = models.EncryptedChar.objects.first()
        assert m1.value == "hello"

        # clear keys cached_property again
        del field1.keys
        settings.FIELD_ENCRYPTION_KEYS = [
            "d244ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
            "f164ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
            "e364ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
        ]

        m1 = models.EncryptedChar.objects.first()
        # can still decrypt after prepending a new key to key list.
        assert m1.value == "hello"
        # make sure keys property did change
        assert keys != field1.keys

        models.EncryptedChar.objects.create(value="world")
        m2 = models.EncryptedChar.objects.last()
        assert m2.value == "world"

    def test_wrong_key(self, settings, db):
        """Raise Exception when invalid key."""
        settings.FIELD_ENCRYPTION_KEYS = [
            "d244ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
            "f164ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
            "e364ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
        ]
        # clear keys cached_property
        field1 = models.EncryptedChar._meta.get_field("value")
        del field1.keys
        # keys will be re-populated here
        models.EncryptedChar.objects.create(value="hello")
        m1 = models.EncryptedChar.objects.first()
        assert m1.value == "hello"

        # clear keys cached_property again
        del field1.keys
        settings.FIELD_ENCRYPTION_KEYS = [
            "f164ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
            "e364ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b",
        ]
        # keys property will now repopulate...
        with pytest.raises(ValueError):
            # Exception raised because of invalid key.
            models.EncryptedChar.objects.first()

    @pytest.mark.parametrize("key", ["primary_key", "db_index", "unique"])
    def test_not_allowed(self, key):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedIntegerField(**{key: True})

    def test_get_integer_field_validators(self):
        f = fields.EncryptedIntegerField()

        # Raises no error
        vals = f.validators
        assert isinstance(vals, (list, tuple)) is True


@pytest.mark.parametrize(
    "model,vals",
    [
        (models.EncryptedText, ["foo", "bar"]),
        (models.EncryptedChar, ["one", "two"]),
        (models.EncryptedEmail, ["a@example.com", "b@example.com"]),
        (models.EncryptedInt, [1, 2]),
        (models.EncryptedDate, [DATE1, DATE2]),
        (models.EncryptedDateTime, [DATETIME1, DATETIME2]),
    ],
)
class TestEncryptedFieldQueries:
    def test_insert(self, db, model, vals):
        """Data stored in DB is actually encrypted."""
        field = model._meta.get_field("value")
        model.objects.create(value=vals[0])
        with connection.cursor() as cur:
            cur.execute("SELECT value FROM %s" % model._meta.db_table)
            data = [field.decrypt(r[0]) for r in cur.fetchall()]

        assert list(map(field.to_python, data)) == [vals[0]]

    def test_insert_and_select(self, db, model, vals):
        """Data round-trips through insert and select."""
        model.objects.create(value=vals[0])
        found = model.objects.get()

        assert found.value == vals[0]

    def test_update_and_select(self, db, model, vals):
        """Data round-trips through update and select."""
        model.objects.create(value=vals[0])
        model.objects.update(value=vals[1])
        found = model.objects.get()

        assert found.value == vals[1]

    def test_lookups_raise_field_error(self, db, model, vals):
        """Lookups except 'isnull' are not allowed."""
        model.objects.create(value=vals[0])
        field_name = model._meta.get_field("value").__class__.__name__
        lookups = set(dj_models.Field.class_lookups) - set(["isnull"])

        for lookup in lookups:
            with pytest.raises(FieldError) as exc:
                model.objects.get(**{"value__" + lookup: vals[0]})
            assert field_name in str(exc.value)
            assert lookup in str(exc.value)
            assert f"does not support '{lookup}' lookups" in str(exc.value)


def test_nullable(db):
    """Encrypted/dual/hash field can be nullable."""
    models.EncryptedNullable.objects.create(value=None)
    found = models.EncryptedNullable.objects.get()

    assert found.value is None


def test_isnull_false_lookup(db):
    """isnull False lookup succeeds on nullable fields"""
    test_val = 3
    models.EncryptedNullable.objects.create(value=None)
    models.EncryptedNullable.objects.create(value=test_val)
    found = models.EncryptedNullable.objects.get(value__isnull=False)

    assert found.value == test_val


def test_isnull_true_lookup(db):
    """isnull True lookup succeeds on nullable fields"""
    test_val = 3
    models.EncryptedNullable.objects.create(value=None)
    models.EncryptedNullable.objects.create(value=test_val)
    found = models.EncryptedNullable.objects.get(value__isnull=True)

    assert found.value is None
