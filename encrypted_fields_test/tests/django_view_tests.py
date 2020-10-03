import datetime
import pytest
from django.test import Client
from django.urls import reverse

from ..forms import DemoModelForm


pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


def test_form_uses_correct_validators():
    data = {
        "name": "Foo",
        "email": "foo@bar.com",
        "date": "1999-10-25",
        "text": "some text",
        "number": 2,
    }
    form = DemoModelForm(data=data)
    assert form.is_valid()

    bad_email = {
        "email": "foo",
        "name": "Foo",
        "date": "1999-10-25",
        "text": "some text",
        "number": 2,
    }
    form = DemoModelForm(data=bad_email)
    assert not form.is_valid()
    assert "Enter a valid email address." in form.errors["email"]
    assert len(form.errors["email"]) == 1

    bad_name = {
        "name": "thisiswaytoolongforthevalidator",
        "email": "foo@bar.com",
        "date": "1999-10-25",
        "text": "some text",
        "number": 2,
    }
    form = DemoModelForm(data=bad_name)
    assert not form.is_valid()
    assert (
        "Ensure this value has at most 10 characters (it has 31)."
        in form.errors["name"]
    )
    assert len(form.errors["name"]) == 1

    bad_date = {
        "name": "thisiswaytoolongforthevalidator",
        "email": "foo@bar.com",
        "date": "not-date",
        "text": "some text",
        "number": 2,
    }
    form = DemoModelForm(data=bad_date)
    assert not form.is_valid()
    assert "Enter a valid date." in form.errors["date"]
    assert len(form.errors["date"]) == 1

    bad_text = {
        "name": "valid",
        "email": "foo@bar.com",
        "date": "1999-10-25",
        "number": 2,
    }
    form = DemoModelForm(data=bad_text)
    assert not form.is_valid()
    assert "This field is required." in form.errors["text"]
    assert len(form.errors["text"]) == 1

    bad_number = {
        "name": "valid",
        "email": "foo@bar.com",
        "date": "1999-10-25",
        "number": "notnumber",
        "text": "foobar",
    }
    form = DemoModelForm(data=bad_number)
    assert not form.is_valid()
    assert "Enter a whole number." in form.errors["number"]
    assert len(form.errors["number"]) == 1


def test_view(client):
    data = {
        "name": "Foo",
        "email": "foo@bar.com",
        "date": "1999-10-25",
        "text": "some text",
        "number": 2,
    }

    new_bad_email = {
        "email": "foo",
        "name": "Foo",
        "date": "1999-10-25",
        "text": "some text",
        "number": 2,
    }

    response = client.post(reverse("demomodel-add"), data=data)
    assert response.status_code == 302  # not 201 because of the redirect on success

    response = client.get(reverse("demomodel-list"))
    assert response.status_code == 200
    response_data = response.context["object_list"].first()
    pk = response_data.id
    assert response_data.name == "Foo"
    assert response_data.email == "foo@bar.com"
    assert response_data.date == datetime.date(1999, 10, 25)
    assert response_data.text == "some text"
    assert response_data.number == 2
    assert response_data.info == ""

    response = client.post(
        reverse("demomodel-update", kwargs={"pk": pk}), data=new_bad_email
    )
    assert "Enter a valid email address" in str(response.content)
