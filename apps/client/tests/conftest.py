import pytest
from faker import Faker
from client.models import Client, Client_Private_Phone, Client_Public_Phone
from user.models import User

fake = Faker()


@pytest.fixture()
def create_super_user(db):
    user = User.objects.create_superuser(username="admin", password="admin")
    return user


@pytest.fixture()
def create_client(db):
    client = Client(

        client_firstname=fake.unique.first_name(),
        client_lastname=fake.unique.last_name(),
        client_father_name=fake.unique.name(),
        client_birthdate=fake.date(),
        client_gender="Male",
        client_telegram=fake.phone_number(),
        client_citizenship=fake.country_code(),
        client_address=fake.address(),
        client_type="Vip"
    )

    private_phone = Client_Private_Phone(
        client_phone_id=1,
        client=client,
        private_phone=fake.phone_number()
    )
    public_phone = Client_Public_Phone(
        client_phone_id=1,
        client=client,
        public_phone=fake.phone_number()
    )

    client.save()
    private_phone.save()
    public_phone.save()
    return client


@pytest.fixture()
def create_client_list(db):
    clients = []
    clients_public_phone = []
    clients_private_phone = []

    for index in range(3):
        client = Client(

            client_firstname=fake.first_name(),
            client_lastname=fake.last_name(),
            client_father_name=fake.name(),
            client_birthdate=fake.date(),
            client_gender="Male",
            client_telegram=fake.phone_number(),
            client_citizenship=fake.country_code(),
            client_address=fake.address(),
            client_type="Vip"
        )

        private_phone = Client_Private_Phone(
            client=client,
            private_phone=fake.phone_number()
        )
        public_phone = Client_Public_Phone(
            client=client,
            public_phone=fake.phone_number()
        )
        clients.append(client)
        clients_private_phone.append(private_phone)
        clients_public_phone.append(public_phone)

    Client.objects.bulk_create(clients)
    Client_Private_Phone.objects.bulk_create(clients_private_phone)
    Client_Public_Phone.objects.bulk_create(clients_public_phone)
    return clients
