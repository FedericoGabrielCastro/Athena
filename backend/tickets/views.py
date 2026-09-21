from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from tickets.catalog import SPEC_BY_SLUG
from tickets.classifier import classifier
from tickets.models import Category, Ticket
from tickets.serializers import (
    CategorySerializer,
    TicketCorrectSerializer,
    TicketCreateSerializer,
    TicketSerializer,
)


def _apply_classification(title: str, body: str) -> tuple[Category, object]:
    result = classifier.classify(title, body)
    category = Category.objects.get(slug=result.category_slug)
    return category, result


@api_view(["GET"])
def category_list(_request):
    categories = Category.objects.all()
    return Response(CategorySerializer(categories, many=True).data)


@api_view(["GET", "POST"])
def ticket_list(request):
    if request.method == "GET":
        tickets = Ticket.objects.select_related("category")
        return Response(TicketSerializer(tickets, many=True).data)

    serializer = TicketCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    title = serializer.validated_data["title"]
    body = serializer.validated_data["body"]
    category, result = _apply_classification(title, body)
    ticket = Ticket.objects.create(
        title=title,
        body=body,
        category=category,
        priority=result.priority,
        confidence=result.confidence,
        tags=result.tags,
        rationale=result.rationale,
        engine=result.engine,
    )
    return Response(TicketSerializer(ticket).data, status=HTTP_201_CREATED)


@api_view(["POST"])
def classify_preview(request):
    serializer = TicketCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    category, result = _apply_classification(
        serializer.validated_data["title"],
        serializer.validated_data["body"],
    )
    return Response(
        {
            "category": CategorySerializer(category).data,
            "priority": result.priority,
            "confidence": result.confidence,
            "tags": result.tags,
            "rationale": result.rationale,
            "engine": result.engine,
            "scores": result.scores,
        }
    )


@api_view(["POST"])
def ticket_correct(request, pk: int):
    serializer = TicketCorrectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    slug = serializer.validated_data["category_slug"]
    if slug not in SPEC_BY_SLUG:
        return Response({"detail": "Unknown category."}, status=HTTP_400_BAD_REQUEST)
    try:
        ticket = Ticket.objects.select_related("category").get(pk=pk)
    except Ticket.DoesNotExist:
        return Response({"detail": "Ticket not found."}, status=HTTP_404_NOT_FOUND)
    ticket.category = Category.objects.get(slug=slug)
    ticket.corrected = True
    ticket.rationale = f"Corregido manualmente a {ticket.category.name}."
    ticket.save(update_fields=["category", "corrected", "rationale", "updated_at"])
    return Response(TicketSerializer(ticket).data)


@api_view(["GET"])
def stats(_request):
    total = Ticket.objects.count()
    by_category = list(
        Ticket.objects.values("category__slug", "category__name", "category__color")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    by_priority = list(
        Ticket.objects.values("priority").annotate(count=Count("id")).order_by("-count")
    )
    return Response(
        {
            "total": total,
            "by_category": [
                {
                    "slug": row["category__slug"],
                    "name": row["category__name"],
                    "color": row["category__color"],
                    "count": row["count"],
                }
                for row in by_category
            ],
            "by_priority": by_priority,
        }
    )
