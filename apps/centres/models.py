from django.db import models


class DiagnosticCentre(models.Model):
    """A physical diagnostic/pathology centre that offers one or more tests."""

    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, help_text="City/area, e.g. 'Pune'")
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.location})"


class DiagnosticTest(models.Model):
    """A single test (e.g. CBC, X-Ray) offered by a centre at a given price."""

    centre = models.ForeignKey(DiagnosticCentre, related_name="tests", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["centre", "name"], name="unique_test_per_centre"),
        ]
        indexes = [models.Index(fields=["centre", "is_active"])]

    def __str__(self):
        return f"{self.name} @ {self.centre.name} - {self.price}"
