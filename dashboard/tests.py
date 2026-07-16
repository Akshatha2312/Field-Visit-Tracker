from django.contrib.auth import get_user_model
from django.test import TestCase


class HomePageTests(TestCase):
    def test_home_page_renders_successfully(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Field Visit Tracker')
        self.assertContains(response, 'Employee Visit Management System')


class LoginFlowTests(TestCase):
    def test_invalid_login_shows_error(self):
        response = self.client.post('/login/', {'username': 'wrong', 'password': 'badpass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct')

    def test_authenticated_user_can_access_dashboard(self):
        User = get_user_model()
        user = User.objects.create_user(username='employee', password='strongpass123')
        self.client.login(username='employee', password='strongpass123')

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
