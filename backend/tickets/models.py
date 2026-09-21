from django.db import models


class Category(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=16, default="#d4a853")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Ticket(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    title = models.CharField(max_length=240)
    body = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="tickets"
    )
    priority = models.CharField(
        max_length=16, choices=Priority.choices, default=Priority.MEDIUM
    )
    confidence = models.FloatField()
    tags = models.JSONField(default=list)
    rationale = models.TextField(blank=True)
    engine = models.CharField(max_length=32, default="local")
    corrected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
