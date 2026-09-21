from django.test import TestCase

from tickets.catalog import CATEGORY_SPECS
from tickets.classifier import LocalTicketClassifier
from tickets.models import Category, Ticket


class ClassifierTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.local = LocalTicketClassifier()

    def _classify(self, title: str, body: str):
        original = self.local._try_ollama
        self.local._try_ollama = lambda *_args, **_kwargs: None
        try:
            return self.local.classify(title, body)
        finally:
            self.local._try_ollama = original

    def test_billing_ticket(self):
        result = self._classify(
            "Double charge on invoice",
            "We were billed twice for the subscription and need a refund.",
        )
        self.assertEqual(result.category_slug, "billing")

    def test_technical_ticket(self):
        result = self._classify(
            "Production 500 error",
            "The API is down and requests timeout after login.",
        )
        self.assertEqual(result.category_slug, "technical")

    def test_security_is_urgent(self):
        result = self._classify(
            "Unauthorized logins",
            "Possible data leak and suspicious access from another country.",
        )
        self.assertEqual(result.category_slug, "security")
        self.assertEqual(result.priority, "urgent")


class ApiTests(TestCase):
    def setUp(self):
        for spec in CATEGORY_SPECS:
            Category.objects.create(
                slug=spec.slug,
                name=spec.name,
                description=spec.description,
                color=spec.color,
            )

    def test_create_ticket_classifies(self):
        response = self.client.post(
            "/api/tickets/",
            {"title": "No puedo iniciar sesión", "body": "La cuenta está bloqueada y no llega el 2FA."},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["category"]["slug"], "account")
        self.assertTrue(Ticket.objects.filter(pk=body["id"]).exists())

    def test_preview_classify(self):
        response = self.client.post(
            "/api/classify/",
            {
                "title": "Add CSV export",
                "body": "Feature request: it would be nice to download reports as CSV.",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["category"]["slug"], "feature")
