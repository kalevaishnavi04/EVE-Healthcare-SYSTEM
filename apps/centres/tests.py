from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DiagnosticCentre, DiagnosticTest

User = get_user_model()


class CentreAndTestTests(APITestCase):
    def setUp(self):
        self.centre = DiagnosticCentre.objects.create(name="City Diagnostics", location="Pune")
        DiagnosticTest.objects.create(centre=self.centre, name="CBC", price=500)

    def test_list_centres_is_public(self):
        response = self.client.get("/api/centres/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_centre_includes_nested_tests(self):
        response = self.client.get(f"/api/centres/{self.centre.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["tests"]), 1)

    def test_filter_tests_by_centre(self):
        other_centre = DiagnosticCentre.objects.create(name="Other Lab", location="Mumbai")
        DiagnosticTest.objects.create(centre=other_centre, name="X-Ray", price=800)

        response = self.client.get(f"/api/tests/?centre={self.centre.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertTrue(all(t["centre"] == self.centre.id for t in results))

    def test_non_admin_cannot_create_centre(self):
        user = User.objects.create_user(username="regular", password="StrongPass123!")
        self.client.force_authenticate(user=user)
        response = self.client.post("/api/centres/", {"name": "New", "location": "Mumbai"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_centre(self):
        admin = User.objects.create_superuser(username="admin", password="StrongPass123!", email="a@a.com")
        self.client.force_authenticate(user=admin)
        response = self.client.post("/api/centres/", {"name": "New", "location": "Mumbai"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_negative_price_rejected(self):
        admin = User.objects.create_superuser(username="admin2", password="StrongPass123!", email="a2@a.com")
        self.client.force_authenticate(user=admin)
        response = self.client.post(
            "/api/tests/", {"centre": self.centre.id, "name": "Bad Test", "price": -10}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
