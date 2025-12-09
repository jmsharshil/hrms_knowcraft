from django.db import models

import uuid


class Interviewer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name

class Slot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    interviewers = models.ManyToManyField("slots.Interviewer", related_name="slots")

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.start} - {self.end} (Booked: {self.is_booked})"
