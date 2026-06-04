from django.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe
from django_ckeditor_5.fields import CKEditor5Field
from shortuuid.django_fields import ShortUUIDField
from taggit.managers import TaggableManager
from accounts.models import User

HOTEL_STATUS = (("Draft","Draft"),("In Review","In Review"),
                ("Live","Live"),("Disabled","Disabled"),("Rejected","Rejected"))

ROOM_TYPES = (("Single","Single"),("Double","Double"),("Twin","Twin"),
              ("King","King"),("Suite","Suite"),("Deluxe","Deluxe"),("Penthouse","Penthouse"))

ICON_TYPE = (("Bootstrap Icons","Bootstrap Icons"),("FontAwesome Icons","FontAwesome Icons"))

RATING = ((1,"★☆☆☆☆"),(2,"★★☆☆☆"),(3,"★★★☆☆"),(4,"★★★★☆"),(5,"★★★★★"))


class Hotel(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotels')
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True, max_length=220, blank=True)
    description = CKEditor5Field(config_name='extends', null=True, blank=True)
    image       = models.ImageField(upload_to='hotel_images/', null=True, blank=True)
    address     = models.CharField(max_length=300)
    city        = models.CharField(max_length=100, null=True, blank=True)
    country     = models.CharField(max_length=100, null=True, blank=True)
    mobile      = models.CharField(max_length=30)
    email       = models.EmailField()
    status      = models.CharField(max_length=20, choices=HOTEL_STATUS, default="Draft")
    featured    = models.BooleanField(default=False)
    views       = models.PositiveIntegerField(default=0)
    tags        = TaggableManager(blank=True)
    date        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def thumbnail(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="60" style="border-radius:4px;">')
        return "—"
    thumbnail.short_description = "Image"

    @property
    def hotel_room_types(self):
        return RoomType.objects.filter(hotel=self)

    @property
    def hotel_gallery(self):
        return HotelGallery.objects.filter(hotel=self)

    @property
    def average_rating(self):
        reviews = self.reviews.filter(active=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None

    @property
    def rating_count(self):
        return self.reviews.filter(active=True).count()


class HotelGallery(models.Model):
    hotel   = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='gallery')
    image   = models.ImageField(upload_to='hotel_gallery/')
    caption = models.CharField(max_length=200, null=True, blank=True)
    date    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hotel.name} – Gallery"


class HotelFeature(models.Model):
    hotel     = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='features')
    icon_type = models.CharField(max_length=30, choices=ICON_TYPE, default="FontAwesome Icons")
    icon      = models.CharField(max_length=100, help_text="e.g. fa-wifi")
    name      = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.hotel.name} – {self.name}"


class HotelFAQ(models.Model):
    hotel    = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=500)
    answer   = models.TextField()
    active   = models.BooleanField(default=True)
    date     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hotel.name}: {self.question[:50]}"


class RoomType(models.Model):
    hotel          = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='room_types')
    type           = models.CharField(max_length=30, choices=ROOM_TYPES)
    slug           = models.SlugField(max_length=150, blank=True)
    price          = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    number_of_beds = models.PositiveIntegerField(default=1)
    description    = CKEditor5Field(config_name='extends', null=True, blank=True)
    thumbnail      = models.ImageField(upload_to='room_types/', null=True, blank=True)
    date           = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hotel','type')

    def __str__(self):
        return f"{self.hotel.name} – {self.type}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.type)
        super().save(*args, **kwargs)

    @property
    def available_rooms(self):
        return self.rooms.filter(is_available=True)


class Room(models.Model):
    hotel        = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type    = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    room_number  = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)
    date         = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hotel','room_number')

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.type}) @ {self.hotel.name}"

    @property
    def price(self):
        return self.room_type.price

    @property
    def number_of_beds(self):
        return self.room_type.number_of_beds


class Review(models.Model):
    hotel  = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    user   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=3)
    active = models.BooleanField(default=True)
    date   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.hotel.name} – {self.rating}★"
