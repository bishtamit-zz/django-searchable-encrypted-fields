from datetime import date, datetime, timedelta
import string
import os

import pytest
from django.core.exceptions import FieldError, ImproperlyConfigured, ValidationError
from django.db import connection, models as dj_models
from django.utils import timezone
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    AdminIntegerFieldWidget,
    AdminBigIntegerFieldWidget,
    AdminEmailInputWidget,
    AdminSplitDateTime,
    AdminDateWidget,
)

from encrypted_fields import fields
from encrypted_fields.management.commands import generate_key

from . import models


pytestmark = pytest.mark.django_db

DATE1 = date.today()
DATE2 = DATE1 + timedelta(days=2)
DATETIME1 = datetime.utcnow()
if os.environ.get("USE_PG"):  # sqlite is not timezone compatible but postgres is.
    DATETIME1 = timezone.now()
DATETIME2 = DATETIME1 + timedelta(minutes=5)


def test_primary_key_not_allowed():
    with pytest.raises(ImproperlyConfigured):
        fields.SearchField(primary_key=True, hash_key="a", encrypted_field_name="value")


def test_must_have_hash_key():
    with pytest.raises(ImproperlyConfigured):
        fields.SearchField(hash_key=None, encrypted_field_name="value")


def test_must_have_encrypted_field_name():
    with pytest.raises(ImproperlyConfigured):
        fields.SearchField(hash_key="aa", encrypted_field_name=None)


def test_generate_key_command(capfd):
    generate_key.Command().execute(no_color=True, force_color=False)
    output = capfd.readouterr()
    # do not include 'new line' (\n) in output
    assert len(output.out[:-1]) == 64
    for char in output.out[:-1]:
        assert char in string.hexdigits


@pytest.mark.parametrize(
    "model,vals",
    [
        (models.SearchText, ["foo", "bar"]),
        (models.SearchChar, ["one", "two"]),
        (models.SearchEmail, ["a@example.com", "b@example.com"]),
        (models.SearchInt, [1, 2]),
        (models.SearchDate, [DATE1, DATE2]),
        (models.SearchDateTime, [DATETIME1, DATETIME2]),
    ],
)
class TestSearchFieldQueries:
    def test_insert(self, db, model, vals):
        """Data stored in DB is actually hashed."""
        field = model._meta.get_field("search")
        model.objects.create(search=vals[0])
        with connection.cursor() as cur:
            cur.execute("SELECT search FROM %s" % model._meta.db_table)
            data = [r[0] for r in cur.fetchall()]

        assert list(map(field.get_prep_value, [vals[0]])) == data

    def test_insert_and_select(self, db, model, vals):
        """Data round-trips through insert and select."""
        model.objects.create(search=vals[0])
        found = model.objects.get()

        assert found.search == vals[0]

    def test_manual_update_and_select(self, db, model, vals):
        """Data round-trips through update and select."""
        obj = model.objects.create(search=vals[0])
        obj.search = vals[1]
        obj.save()
        found = model.objects.get()

        assert found.search == vals[1]

    def test_update_and_select(self, db, model, vals):
        """Data round-trips through update and select."""
        model.objects.create(search=vals[0])
        model.objects.update(search=vals[1])
        found = model.objects.get()

        # This fails because 'update' is at SQL level, can't do anything about this.
        # assert found.search == vals[1]
        assert found.search == vals[0]  # value will not have updated...boo!

        # updating requires changes to both fields
        model.objects.update(search=vals[1], value=vals[1])
        found = model.objects.get()
        assert found.search == vals[1]

    def test_lookups_raise_field_error(self, db, model, vals):
        """Lookups except 'isnull' and 'exact' are not allowed."""
        model.objects.create(search=vals[0])
        field_name = model._meta.get_field("search").__class__.__name__
        lookups = set(dj_models.Field.class_lookups) - set(["isnull", "exact"])

        for lookup in lookups:
            with pytest.raises(FieldError) as exc:
                model.objects.get(**{"search__" + lookup: vals[0]})
            assert field_name in str(exc.value)
            assert lookup in str(exc.value)
            assert f"does not support '{lookup}' lookups" in str(exc.value)


def test_validation():
    """Test SearchField uses Validators from associated data field."""
    # has max_len=25, so will fail
    m = models.SearchChar(search="12345678901234567890qwertyuiop")
    with pytest.raises(ValidationError):
        m.full_clean(exclude=["value"])
    # has MaxValue = 10
    m = models.SearchInt(search=12)
    with pytest.raises(ValidationError):
        m.full_clean(exclude=["value"])
    # has Email validator
    m = models.SearchEmail(search="sometext.com")
    with pytest.raises(ValidationError):
        m.full_clean(exclude=["value"])
    # has SearchField has max_len of 66, this should pass despite this
    m = models.SearchText(
        search="12345678901234567890123456789012345678901234567890123456789012345678901234567890qwertyuiop"
    )
    m.full_clean(exclude=["value"])


def test_form_field():
    """Test widget swapping when called by Admin Panel"""
    kwargs = {"widget": AdminTextInputWidget}
    m = models.SearchInt(search=9)
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminIntegerFieldWidget)

    m = models.SearchBigInt(search=99)
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminBigIntegerFieldWidget)

    m = models.SearchSmallInt(search=99)
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminIntegerFieldWidget)

    m = models.SearchPosSmallInt(search=99)
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminIntegerFieldWidget)

    m = models.SearchPosInt(search=99)
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminIntegerFieldWidget)

    m = models.SearchEmail(search="foo@bar.com")
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminEmailInputWidget)

    m = models.SearchChar(search="hello")
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminTextInputWidget)

    m = models.SearchDate(search="2019-03-03")
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminDateWidget)

    m = models.SearchDateTime(search="2019-03-03")
    x = m._meta.get_field("search").formfield(**kwargs)
    assert isinstance(x.widget, AdminSplitDateTime)
