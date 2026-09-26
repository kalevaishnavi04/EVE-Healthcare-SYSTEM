from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    def test_signup_success(self):
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
        }
        response = self.client.post("/api/auth/signup/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_signup_duplicate_email_rejected(self):
        User.objects.create_user(username="existing", email="dup@example.com", password="StrongPass123!")
        payload = {"username": "another", "email": "dup@example.com", "password": "StrongPass123!"}
        response = self.client.post("/api/auth/signup/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_weak_password_rejected(self):
        payload = {"username": "weakpw", "email": "weak@example.com", "password": "123"}
        response = self.client.post("/api/auth/signup/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(username="loginuser", password="StrongPass123!")
        response = self.client.post(
            "/api/auth/login/", {"username": "loginuser", "password": "StrongPass123!"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_wrong_password_rejected(self):
        User.objects.create_user(username="loginuser2", password="StrongPass123!")
        response = self.client.post(
            "/api/auth/login/", {"username": "loginuser2", "password": "wrong"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
