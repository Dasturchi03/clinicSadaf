from faker import Faker
import json
from rest_framework.test import APIClient
from category.models import Category
from category.api.serializers import CategorySerializer

fake = Faker()


def test_category_create(create_super_user):
    """ Creating category with None relations """

    url = "/categories"

    data = {
        "category_title_ru": fake.name(),
        "category_title_en": fake.name(),
        "category_title_uz": fake.name()
    }

    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = CategorySerializer(data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.save()
    assert serializer.validated_data == data
    assert serializer.errors == {}

    response = client.post(url, json.dumps(serializer.data), content_type="application/json")

    category = Category.objects.first()

    assert response.status_code == 201
    assert category is not None


def test_category_create_with_relation(create_super_user, create_work_for_category):
    """ Creating category with relations """

    url = "/categories"

    data = {
        "category_title_ru": fake.name(),
        "category_title_en": fake.name(),
        "category_title_uz": fake.name(),
        "work_category": [
            {
                "work_id": create_work_for_category.work_id
            }
        ]
    }
    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = CategorySerializer(data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.save()
    assert serializer.validated_data == data
    assert serializer.errors == {}

    response = client.post(url, json.dumps(data), content_type="application/json")

    category = Category.objects.first()

    assert response.status_code == 201
    assert category is not None
    assert category.work_category.count() == 1


def test_category_list(create_super_user, create_category_list):
    """ Retrieving category list"""

    url = f"/categories?page=1&page_size=10"
    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = CategorySerializer(create_category_list, many=True)
    for index, serialized_category in enumerate(serializer.data):
        assert serialized_category['category_id'] == create_category_list[index].category_id
        assert serialized_category['category_title_ru'] == create_category_list[index].category_title_ru
        assert serialized_category['category_title_en'] == create_category_list[index].category_title_en
        assert serialized_category['category_title_uz'] == create_category_list[index].category_title_uz

        work_categories = serialized_category.get('work_category')
        for work_instance in work_categories:
            assert work_instance.get("work_id") == create_category_list[index].work_category.first().work_id
            assert work_instance.get("work_title") == create_category_list[index].work_category.first().work_title

    response = client.get(url, content_type="application/json")
    assert response.status_code == 200


def test_category_instance(create_super_user, create_category):
    """ Retrieving category instance"""

    url = f"/categories/{create_category.category_id}"
    client = APIClient()
    client.force_authenticate(user=create_super_user)

    serializer = CategorySerializer(create_category)
    assert serializer.data['category_id'] == create_category.category_id
    assert serializer.data['category_title_ru'] == create_category.category_title_ru
    assert serializer.data['category_title_en'] == create_category.category_title_en
    assert serializer.data['category_title_uz'] == create_category.category_title_uz

    work_category = serializer.data.get('work_category')
    assert work_category[0].get("work_id") == create_category.work_category.first().work_id
    assert work_category[0].get("work_title") == create_category.work_category.first().work_title

    response = client.get(url, content_type="application/json")

    category = Category.objects.first()

    assert response.status_code == 200
    assert category is not None


def test_category_update(create_super_user, create_category, create_work_for_category):
    """ Updating category with None relation """

    url = f"/categories/{create_category.category_id}"
    data = {
        "category_title_ru": fake.name(),
        "category_title_en": fake.name(),
        "category_title_uz": fake.name(),
    }

    client = APIClient()
    client.force_authenticate(user=create_super_user)
    response_get = client.get(url, content_type="application/json")

    serializer = CategorySerializer(create_category, data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.save()

    assert json.loads(response_get.content)["category_title_ru"] != create_category.category_title_ru
    assert json.loads(response_get.content)["category_title_en"] != create_category.category_title_en
    assert json.loads(response_get.content)["category_title_uz"] != create_category.category_title_en

    response_patch = client.patch(url, json.dumps(serializer.data), content_type="application/json")

    assert response_patch.status_code == 200
    assert json.loads(response_get.content)["category_title_ru"] != json.loads(response_patch.content)["category_title_ru"]
    assert json.loads(response_get.content)["category_title_en"] != json.loads(response_patch.content)["category_title_en"]
    assert json.loads(response_get.content)["category_title_uz"] != json.loads(response_patch.content)["category_title_uz"]
    assert json.loads(response_get.content)["work_category"][0].get("work_id") == json.loads(response_patch.content)["work_category"][0].get("work_id")


def test_category_update_with_relation(create_super_user, create_category, create_work_for_category):
    """ Updating category with relation """

    url = f"/categories/{create_category.category_id}"
    data = {
        "category_title_ru": fake.name(),
        "category_title_en": fake.name(),
        "category_title_uz": fake.name(),
        "work_category": [
            {
                "work_id": create_work_for_category.work_id
            }
        ]

    }

    client = APIClient()
    client.force_authenticate(user=create_super_user)
    response_get = client.get(url, content_type="application/json")

    serializer = CategorySerializer(create_category, data=data)
    assert serializer.is_valid(raise_exception=True)
    assert serializer.save()

    assert json.loads(response_get.content)["category_title_ru"] != create_category.category_title_ru
    assert json.loads(response_get.content)["category_title_en"] != create_category.category_title_en
    assert json.loads(response_get.content)["category_title_uz"] != create_category.category_title_en
    assert json.loads(response_get.content)["work_category"][0].get("work_id") != create_category.work_category.first().work_id

    response_patch = client.patch(url, json.dumps(data), content_type="application/json")

    assert response_patch.status_code == 200
    assert json.loads(response_get.content)["category_title_ru"] != json.loads(response_patch.content)["category_title_ru"]
    assert json.loads(response_get.content)["category_title_en"] != json.loads(response_patch.content)["category_title_en"]
    assert json.loads(response_get.content)["category_title_uz"] != json.loads(response_patch.content)["category_title_uz"]
    assert json.loads(response_get.content)["work_category"][0].get("work_id") != json.loads(response_patch.content)["work_category"][0].get("work_id")

