from faker import Faker
import json
from rest_framework.test import APIClient
from client.models import Client, Client_Private_Phone, Client_Public_Phone
from client.api.serializers import ClientSerializer, ClientSerializerData, ClientListSerializer

fake = Faker()


def test_client_create(create_super_user):
    """ Creating client """

    url = "/clients"

    data = {
      "client_firstname": fake.first_name(),
      "client_lastname": fake.last_name(),
      "client_father_name": fake.name(),
      "client_birthdate": fake.date(pattern="%d-%m-%Y"),
      "client_gender": "Male",
      "client_citizenship": "UZ",
      "client_public_phone": [
        {
          "public_phone": fake.phone_number()
        }
      ],
      "client_private_phone": [
        {
          "private_phone": fake.phone_number()
        }
      ],
      "client_telegram": fake.phone_number(),
      "client_address": fake.address(),
      "client_type": "Vip"
    }
    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = ClientSerializer(data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.errors == {}

    response = client.post(url, json.dumps(serializer.data), content_type="application/json")

    client_instance = Client.objects.first()
    assert response.status_code == 201
    assert client_instance is not None


def test_client_create_with_non_required_fields(create_super_user):
    """ Creating client with non-required fields"""

    url = "/clients"

    data = {
      "client_firstname": fake.first_name(),
      "client_lastname": fake.last_name(),
      "client_birthdate": fake.date(pattern="%d-%m-%Y"),
      "client_gender": "Male",
      "client_citizenship": fake.country_code(),
      "client_public_phone": [
        {
          "public_phone": fake.phone_number()
        }
      ],
      "client_telegram": fake.phone_number(),
      "client_type": "Vip"
    }
    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = ClientSerializer(data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.errors == {}

    response = client.post(url, json.dumps(serializer.data), content_type="application/json")

    client_instance = Client.objects.first()
    assert response.status_code == 201
    assert client_instance is not None


def test_client_list(create_super_user, create_client_list):
    """ Retrieving client list"""
    url = f"/clients?client_gender=Male&client_type=Vip&client_citizenship={create_client_list[0].client_citizenship}"
    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = ClientListSerializer(create_client_list, many=True)
    for index, serialized_clients in enumerate(serializer.data):
        assert serialized_clients['client_id'] == create_client_list[index].client_id
        assert serialized_clients['client_firstname'] == create_client_list[index].client_firstname
        assert serialized_clients['client_lastname'] == create_client_list[index].client_lastname
        assert serialized_clients['client_birthdate'] == create_client_list[index].client_birthdate

        private_phones = serialized_clients.get('client_private_phone')
        for phone in private_phones:
            assert phone.get("client_phone_id") == create_client_list[index].client_private_phone.first().client_phone_id
            assert phone.get("private_phone") == create_client_list[index].client_private_phone.first().private_phone

        public_phones = serialized_clients.get('client_public_phone')
        for phone in public_phones:
            assert phone.get("client_phone_id") == create_client_list[index].client_public_phone.first().client_phone_id
            assert phone.get("public_phone") == create_client_list[index].client_public_phone.first().public_phone

    response = client.get(url, content_type="application/json")
    assert response.status_code == 200


def test_client_instance(create_super_user, create_client):
    """ Retrieving client instance"""

    url = f"/clients/{create_client.client_id}"
    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = ClientSerializerData(create_client)
    assert serializer.data['client_id'] == create_client.client_id
    assert serializer.data['client_firstname'] == create_client.client_firstname
    assert serializer.data['client_lastname'] == create_client.client_lastname
    assert serializer.data['client_father_name'] == create_client.client_father_name

    private_phones = serializer.data.get('client_private_phone')
    assert private_phones[0].get("client_phone_id") == create_client.client_private_phone.first().client_phone_id
    assert private_phones[0].get("private_phone") == create_client.client_private_phone.first().private_phone

    public_phone = serializer.data.get('client_public_phone')
    assert public_phone[0].get("client_phone_id") == create_client.client_public_phone.first().client_phone_id
    assert public_phone[0].get("public_phone") == create_client.client_public_phone.first().public_phone

    response = client.get(url, content_type="application/json")

    client = Client.objects.first()

    assert response.status_code == 200
    assert client is not None


def test_client_update(create_super_user, create_client):
    """ Updating client """

    url = f"/clients/{create_client.client_id}"

    data = {
        "client_firstname": fake.first_name(),
        "client_lastname": fake.last_name(),
        "client_father_name": fake.name(),
        "client_birthdate": fake.date(pattern="%d-%m-%Y"),
        "client_gender": "Male",
        "client_citizenship": fake.country_code(),
        "client_public_phone": [
            {
                "public_phone": fake.phone_number()
            }
        ],
        "client_private_phone": [
            {
                "private_phone": fake.phone_number()
            }
        ],
        "client_telegram": fake.phone_number(),
        "client_address": fake.address(),
        "client_type": "Vip"
    }

    client = APIClient()
    client.force_authenticate(user=create_super_user)

    response_get = client.get(url, content_type="application/json")

    serializer = ClientSerializerData(create_client, data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.save()

    assert json.loads(response_get.content)["client_firstname"] != create_client.client_firstname
    assert json.loads(response_get.content)["client_lastname"] != create_client.client_lastname
    assert json.loads(response_get.content)["client_father_name"] != create_client.client_father_name
    assert json.loads(response_get.content)["client_public_phone"][0].get("public_phone") != create_client.client_public_phone.first().public_phone
    assert json.loads(response_get.content)["client_private_phone"][0].get("private_phone") != create_client.client_private_phone.first().private_phone

    response_patch = client.patch(url, json.dumps(serializer.data), content_type="application/json")

    assert response_patch.status_code == 200
    assert json.loads(response_get.content)["client_firstname"] != json.loads(response_patch.content)["client_firstname"]
    assert json.loads(response_get.content)["client_lastname"] != json.loads(response_patch.content)["client_lastname"]
    assert json.loads(response_get.content)["client_father_name"] != json.loads(response_patch.content)["client_father_name"]
    assert json.loads(response_get.content)["client_public_phone"][0].get("public_phone") != json.loads(response_patch.content)["client_public_phone"][0].get("public_phone")
    assert json.loads(response_get.content)["client_private_phone"][0].get("private_phone") != json.loads(response_patch.content)["client_private_phone"][0].get("private_phone")


def test_client_update_with_non_required_fields(create_super_user, create_client):
    """ Creating client with non-required fields"""

    url = f"/clients/{create_client.client_id}"

    data = {
      "client_firstname": fake.first_name(),
      "client_lastname": fake.last_name(),
      "client_birthdate": fake.date(pattern="%d-%m-%Y"),
      "client_gender": "Male",
      "client_citizenship": fake.country_code(),
      "client_public_phone": [
        {
            'client_phone_id': 1,
            "public_phone": fake.phone_number()
        }
      ],
      "client_telegram": fake.phone_number(),
      "client_type": "Vip"
    }
    client = APIClient()
    client.force_authenticate(user=create_super_user)
    response_get = client.get(url, content_type="application/json")

    serializer = ClientSerializerData(create_client, data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.save()

    assert json.loads(response_get.content)["client_firstname"] != create_client.client_firstname
    assert json.loads(response_get.content)["client_lastname"] != create_client.client_lastname
    assert json.loads(response_get.content)["client_father_name"] == create_client.client_father_name
    assert json.loads(response_get.content)["client_public_phone"][0].get("public_phone") != create_client.client_public_phone.first().public_phone

    response_patch = client.patch(url, json.dumps(serializer.data), content_type="application/json")
    assert response_patch.status_code == 200
    assert json.loads(response_get.content)["client_firstname"] != json.loads(response_patch.content)["client_firstname"]
    assert json.loads(response_get.content)["client_lastname"] != json.loads(response_patch.content)["client_lastname"]
    assert json.loads(response_get.content)["client_father_name"] == json.loads(response_patch.content)["client_father_name"]
    assert json.loads(response_get.content)["client_public_phone"][0].get("public_phone") != json.loads(response_patch.content)["client_public_phone"][0].get("public_phone")
    assert json.loads(response_get.content)["client_private_phone"][0].get("private_phone") == json.loads(response_patch.content)["client_private_phone"][0].get("private_phone")
