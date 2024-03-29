import os
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError


class Airport(models.Model):
    name = models.CharField(max_length=100)
    closest_big_city = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class AirplaneType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


def airplane_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/airplanes/", filename)


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes"
    )
    image = models.ImageField(null=True, upload_to=airplane_image_file_path)

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="orders"
    )

    def __str__(self):
        return f"created_at: {self.created_at}"

    class Meta:
        ordering = ["-created_at"]


class Route(models.Model):
    source = models.ForeignKey(
        Airport, on_delete=models.CASCADE,
        related_name="departures"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="arrivals"
    )
    distance = models.IntegerField()

    def __str__(self):
        return (f"source: {self.source.name}, "
                f"destination: {self.destination.name}")

    class Meta:
        unique_together = ["source", "destination"]


class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew)

    def __str__(self):
        return (f"{self.airplane.name}-"
                f"{self.departure_time}:{self.arrival_time}")

    class Meta:
        default_related_name = "flights"
        ordering = ["departure_time"]


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="taken_seats"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"row: {self.row}, seat: {self.seat}"

    class Meta:
        default_related_name = "tickets"
        unique_together = ("seat", "row", "flight")

    @staticmethod
    def validate_seat(
            seat: int,
            num_seats: int,
            row: int,
            num_rows: int,
            error_to_raise
    ) -> None:
        if not (1 <= seat <= num_seats):
            raise error_to_raise({
                "seat": f"seat must be in the range [1, {num_seats}]"
            })

        if not (1 <= row <= num_rows):
            raise error_to_raise({
                "row": f"row must be in the range [1, {num_rows}]"
            })

    def clean(self):
        Ticket.validate_seat(
            self.seat, self.flight.airplane.seats_in_row,
            self.row, self.flight.airplane.rows, ValidationError
        )
