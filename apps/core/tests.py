from django.test import TestCase
from django.urls import reverse


class DashboardTests(TestCase):
    def test_dashboard_responds_successfully(self):
        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MotoService")
        self.assertTemplateUsed(response, "core/dashboard.html")
