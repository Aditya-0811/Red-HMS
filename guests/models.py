from django.db import models
from shortuuid.django_fields import ShortUUIDField
from accounts.models import User
from rooms.models import Hotel, RoomType, Room

PAYMENT_STATUS = (
    ("initiated","Initiated"),("processing","Processing"),("paid","Paid"),
    ("pending","Pending"),("cancelled","Cancelled"),("failed","Failed"),
    ("refunding","Refunding"),("refunded","Refunded"),("expired","Expired"),
)
DISCOUNT_TYPE = (("Percentage","Percentage"),("Flat Rate","Flat Rate"))


class Coupon(models.Model):
    hotel            = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True)
    code             = models.CharField(max_length=100, unique=True)
    discount_type    = models.CharField(max_length=20, choices=DISCOUNT_TYPE, default="Percentage")
    discount         = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    redemption_limit = models.PositiveIntegerField(default=100)
    valid_from       = models.DateField()
    valid_to         = models.DateField()
    active           = models.BooleanField(default=True)
    date             = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} – {self.discount_type} {self.discount}"


class Reservation(models.Model):
    booking_id  = ShortUUIDField(unique=True, length=10, max_length=20,
                                 alphabet="abcdefghijklmnopqrstuvwxyz1234567890")
    success_id  = ShortUUIDField(length=100, max_length=200,
                                 alphabet="abcdefghijklmnopqrstuvwxyz1234567890")
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reservations')
    hotel       = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True,
                                    related_name='reservations')
    room_type   = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True)
    room        = models.ManyToManyField(Room, blank=True)
    coupons     = models.ManyToManyField(Coupon, blank=True)
    full_name   = models.CharField(max_length=300)
    email       = models.EmailField()
    phone       = models.CharField(max_length=30, null=True, blank=True)
    check_in_date  = models.DateField()
    check_out_date = models.DateField()
    total_days     = models.PositiveIntegerField(default=1)
    num_adults     = models.PositiveIntegerField(default=1)
    num_children   = models.PositiveIntegerField(default=0)
    before_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total           = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    saved           = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_status  = models.CharField(max_length=30, choices=PAYMENT_STATUS, default="initiated")
    is_active       = models.BooleanField(default=True)
    checked_in      = models.BooleanField(default=False)
    checked_out     = models.BooleanField(default=False)
    checked_in_tracker  = models.BooleanField(default=False,
                                              help_text="System use – do not modify")
    checked_out_tracker = models.BooleanField(default=False,
                                              help_text="System use – do not modify")
    stripe_payment_intent = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"#{self.booking_id} – {self.full_name}"

    @property
    def nights(self):
        return (self.check_out_date - self.check_in_date).days


class Bookmark(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='bookmarks')
    date  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','hotel')

    def __str__(self):
        return f"{self.user.username} ♥ {self.hotel.name}"


class ActivityLog(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE,
                                    related_name='activity_logs')
    staff       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=500)
    date        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Log: {self.reservation.booking_id} – {self.description[:40]}"
