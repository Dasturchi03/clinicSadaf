import pytest
from faker import Faker
from category.models import Category
from user.models import User
from work.models import Work

fake = Faker()


@pytest.fixture()
def create_super_user(db):
    user = User.objects.create_superuser(username="admin", password="admin")
    return user


@pytest.fixture()
def create_category(db):
    category = Category.objects.create(
        category_id=fake.random_int(),
        category_title_ru=fake.name(),
        category_title_en=fake.name(),
        category_title_uz=fake.name(),
    )
    work = Work.objects.create(
        work_id=fake.random_int(),
        work_type="Common",
        work_salary_type="Fixed",
        work_title=fake.name(),
        work_time=fake.random_int(),
        work_basic_price=fake.random_int(),
        work_vip_price=fake.random_int(),
        work_discount_price=fake.random_int(),
        work_discount_percent=fake.random_int(),
        work_fixed_salary_amount=fake.random_int(),
        work_hybrid_salary_amount=fake.random_int(),
    )
    work.category.add(category)
    return category


@pytest.fixture()
def create_category_list(db):
    categories = []
    works = []
    for index in range(3):
        category = Category(
            category_id=fake.random_int(),
            category_title_ru=fake.name(),
            category_title_en=fake.name(),
            category_title_uz=fake.name(),
        )
        work = Work(
            work_id=fake.random_int(),
            work_type="Common",
            work_salary_type="Fixed",
            work_title=fake.name(),
            work_time=fake.random_int(),
            work_basic_price=fake.random_int(),
            work_vip_price=fake.random_int(),
            work_discount_price=fake.random_int(),
            work_discount_percent=fake.random_int(),
            work_fixed_salary_amount=fake.random_int(),
            work_hybrid_salary_amount=fake.random_int(),
        )
        work.category.add(category)
        categories.append(category)
        works.append(work)

    Category.objects.bulk_create(categories)
    Work.objects.bulk_create(works)
    return categories


@pytest.fixture()
def create_work_for_category(db):
    work = Work.objects.create(work_id=fake.random_int(), work_title=fake.name(), work_time=fake.random_int())
    return work
