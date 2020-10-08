import datetime
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from ..models import DemoModel


pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


def test_crud(api_client):
    today = datetime.date.today()
    today_string = today.strftime("%Y-%m-%d")
    data = {
        "name": "Foo",
        "email": "foo@bar.com",
        "date": "1999-10-25",
        "text": "some text",
        "number": 2,
    }
    response = api_client.post(reverse("api-demomodel-list"), data=data)
    assert response.status_code == status.HTTP_201_CREATED

    response = api_client.get(reverse("api-demomodel-list"))
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    pk = response_data[0]["id"]
    assert response_data[0]["name"] == "Foo"
    assert response_data[0]["email"] == "foo@bar.com"
    assert response_data[0]["date"] == "1999-10-25"
    assert response_data[0]["text"] == "some text"
    assert response_data[0]["number"] == 2
    assert response_data[0]["info"] == ""
    assert response_data[0]["default_date"] == today_string
    assert response_data[0]["default_number"] == 1
    assert response_data[0]["default_char"] == "foo default"

    new_bad_email = {"email": "foo"}
    response = api_client.patch(
        reverse("api-demomodel-detail", kwargs={"pk": pk}), data=new_bad_email
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    new_bad_number = {"number": "foo"}
    response = api_client.patch(
        reverse("api-demomodel-detail", kwargs={"pk": pk}), data=new_bad_number
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    new_bad_date = {"date": "foo"}
    response = api_client.patch(
        reverse("api-demomodel-detail", kwargs={"pk": pk}), data=new_bad_date
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    new_bad_name = {"name": "toolongforthevalidator"}
    response = api_client.patch(
        reverse("api-demomodel-detail", kwargs={"pk": pk}), data=new_bad_name
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    new_email = {"email": "a@b.com"}
    response = api_client.patch(
        reverse("api-demomodel-detail", kwargs={"pk": pk}), data=new_email
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["email"] == "a@b.com"
    # other data is still unchanged.
    assert response_data["name"] == "Foo"
    assert response_data["date"] == "1999-10-25"
    assert response_data["text"] == "some text"
    assert response_data["number"] == 2
    assert response_data["info"] == ""
    assert response_data["default_date"] == today_string
    assert response_data["default_number"] == 1
    assert response_data["default_char"] == "foo default"

    # Test SearchFields properly populated
    assert DemoModel.objects.get(email="a@b.com")
    assert DemoModel.objects.get(name="Foo")
    assert DemoModel.objects.get(number=2)
    assert DemoModel.objects.get(date=datetime.date(1999, 10, 25))
