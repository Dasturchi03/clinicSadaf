from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from disease.models import Disease
from work.models import Work
from user.models import User


class BookTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_superuser(username="admin", password="admin")
        self.client.force_authenticate(user=self.user)

        self.work_data = {
            "work_id": 1,
            "work_title": "Test Work",
            "work_time": 10
        }
        self.work_instance = Work.objects.create(**self.work_data)

        self.disease_data = {
            'disease_title_ru': 'Test Disease',
            'disease_title_en': 'Test Disease',
            'disease_title_uz': "Test Disease"
        }
        self.disease_instance = Disease.objects.create(**self.disease_data)

        self.work_instance.disease.add(self.disease_instance)

    def test_disease_list(self):
        response = self.client.get('/diseases')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_disease_single(self):
        response = self.client.get(f'/diseases/{self.disease_instance.disease_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['disease_title'], self.disease_instance.disease_title)

    def test_disease_create(self):
        response = self.client.post('/diseases', self.disease_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Disease.objects.count(), 2)

    def test_update_book(self):
        work_data = {
            "work_id": 2,
            "work_title": "Test Work",
            "work_time": 10
        }
        work_instance = Work.objects.create(**work_data)

        updated_data = {
            'disease_title_ru': 'Update Disease',
            'disease_title_en': 'Update Disease',
            'disease_title_uz': "Update Disease"
        }

        self.disease_instance.work_disease.clear()
        work_instance.disease.add(self.disease_instance)
        response = self.client.patch(f'/diseases/{self.disease_instance.disease_id}', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.disease_instance.refresh_from_db()
        self.assertEqual(self.disease_instance.disease_title_ru, updated_data['disease_title_ru'])
        self.assertEqual(self.disease_instance.disease_title_en, updated_data['disease_title_en'])
        self.assertEqual(self.disease_instance.disease_title_uz, updated_data['disease_title_uz'])
        self.assertEqual(self.disease_instance.work_disease.all().first(), work_instance)

    def test_delete_book(self):
        disease_data = {
            'disease_title_ru': 'Архив',
            'disease_title_en': 'Архив',
            'disease_title_uz': "Архив"
        }
        Disease.objects.create(**disease_data)
        response = self.client.delete(f'/diseases/{self.disease_instance.disease_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(Disease.objects.filter(deleted=True)), 1)
