from rest_framework import serializers

from tickets.models import Category, Ticket


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "slug", "name", "description", "color")


class TicketSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "title",
            "body",
            "category",
            "priority",
            "confidence",
            "tags",
            "rationale",
            "engine",
            "corrected",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class TicketCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=240)
    body = serializers.CharField()


class TicketCorrectSerializer(serializers.Serializer):
    category_slug = serializers.SlugField()
