from django.db import models
from accounts.models import User

class Report(models.Model):
    TYPES = (("Revenue","Revenue"),("Occupancy","Occupancy"),
             ("Guest","Guest"),("Booking","Booking"))
    title        = models.CharField(max_length=200)
    report_type  = models.CharField(max_length=30, choices=TYPES)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_from    = models.DateField()
    data_to      = models.DateField()
    notes        = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.report_type}: {self.title}"
