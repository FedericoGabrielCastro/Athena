from django.core.management.base import BaseCommand

from tickets.catalog import CATEGORY_SPECS
from tickets.classifier import classifier
from tickets.models import Category, Ticket

SAMPLE_TICKETS = (
    (
        "Cobro duplicado en la factura de septiembre",
        "Nos debitaron dos veces el plan Team. Pedimos reembolso del cargo extra y la factura corregida.",
    ),
    (
        "Error 500 al subir archivos en producción",
        "Desde esta mañana el upload falla con timeout y error 500. Afecta a todos los usuarios.",
    ),
    (
        "¿Pueden agregar exportación CSV?",
        "Sería útil descargar los reportes en CSV para el cierre mensual del equipo de finanzas.",
    ),
    (
        "No llega el código de 2FA",
        "La cuenta quedó bloqueada y no recibo el código para iniciar sesión. Necesito recuperar el acceso.",
    ),
    (
        "Inicios de sesión no autorizados",
        "Vimos logins sospechosos desde otro país. Posible acceso no autorizado a la cuenta admin.",
    ),
    (
        "¿Dónde está la documentación de webhooks?",
        "Duda de onboarding: no encuentro cómo registrar un endpoint de webhooks en la API.",
    ),
)


class Command(BaseCommand):
    help = "Create categories and sample classified tickets."

    def handle(self, *args, **options):
        for spec in CATEGORY_SPECS:
            Category.objects.update_or_create(
                slug=spec.slug,
                defaults={
                    "name": spec.name,
                    "description": spec.description,
                    "color": spec.color,
                },
            )

        created = 0
        if not Ticket.objects.exists():
            for title, body in SAMPLE_TICKETS:
                result = classifier.classify(title, body)
                category = Category.objects.get(slug=result.category_slug)
                Ticket.objects.create(
                    title=title,
                    body=body,
                    category=category,
                    priority=result.priority,
                    confidence=result.confidence,
                    tags=result.tags,
                    rationale=result.rationale,
                    engine=result.engine,
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Category.objects.count()} categories and {created} sample tickets."
            )
        )
