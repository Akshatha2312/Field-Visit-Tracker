from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from employee.models import Employee

from .middleware import GracefulExceptionMiddleware


class ErrorPageTests(TestCase):
    def test_unknown_url_renders_custom_404_page(self):
        response = self.client.get('/definitely-not-a-real-route/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')
        self.assertContains(response, 'Page not found', status_code=404)

    def test_permission_denied_renders_custom_403_page(self):
        user = get_user_model().objects.create_user(username='employee403', password='secret123')
        Employee.objects.create(
            user=user,
            name='Restricted User',
            email='restricted@example.com',
            password='secret123',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('employee:list'))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'errors/403.html')
        self.assertContains(response, 'Access denied', status_code=403)

    def test_database_exception_renders_custom_500_page(self):
        request = RequestFactory().get('/any/')
        request.user = None
        middleware = GracefulExceptionMiddleware(lambda req: None)

        response = middleware.process_exception(request, DatabaseError('Simulated database issue'))

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, 'Something went wrong', status_code=500)
