from django.db import models
from shortuuid.django_fields import ShortUUIDField
from accounts.models import User
from guests.models import Reservation
from rooms.models import Room

PAYMENT_METHOD = (("Stripe","Stripe"),("PayPal","PayPal"),
                  ("Cash","Cash"),("Bank Transfer","Bank Transfer"))

PAYMENT_STATUS = (("initiated","Initiated"),("processing","Processing"),
                  ("paid","Paid"),("failed","Failed"),("refunded","Refunded"))

SERVICE_TYPE = (("Food","Food"),("Cleaning","Cleaning"),("Laundry","Laundry"),
                ("Transport","Transport"),("Technical","Technical"),
                ("Spa","Spa"),("Other","Other"))


class Invoice(models.Model):
    invoice_id  = ShortUUIDField(unique=True, length=10, max_length=20,
                                 alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE,
                                       related_name='invoice')
    issued_by   = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='issued_invoices')
    subtotal    = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount    = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax         = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total       = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes       = models.TextField(null=True, blank=True)
    issued_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_date"]

    def __str__(self):
        return f"Invoice #{self.invoice_id} – {self.reservation.full_name}"


class Payment(models.Model):
    payment_id            = ShortUUIDField(unique=True, length=10, max_length=20,
                                           alphabet="abcdefghijklmnopqrstuvwxyz1234567890")
    reservation           = models.ForeignKey(Reservation, on_delete=models.CASCADE,
                                              related_name='payments')
    amount                = models.DecimalField(max_digits=12, decimal_places=2)
    method                = models.CharField(max_length=30, choices=PAYMENT_METHOD, default="Stripe")
    status                = models.CharField(max_length=30, choices=PAYMENT_STATUS, default="initiated")
    stripe_payment_intent = models.CharField(max_length=300, null=True, blank=True)
    stripe_charge_id      = models.CharField(max_length=300, null=True, blank=True)
    date                  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Payment #{self.payment_id} – {self.status} – ${self.amount}"


class RoomService(models.Model):
    reservation  = models.ForeignKey(Reservation, on_delete=models.CASCADE,
                                     related_name='room_services')
    room         = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE)
    description  = models.CharField(max_length=500, null=True, blank=True)
    price        = models.DecimalField(max_digits=8, decimal_places=2)
    date         = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.service_type} – ${self.price}"
