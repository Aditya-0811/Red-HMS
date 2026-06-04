from django import forms
from .models import RoomType

class RoomAvailabilityForm(forms.Form):
    checkin  = forms.DateField(widget=forms.DateInput(attrs={'class':'with-border','type':'date'}))
    checkout = forms.DateField(widget=forms.DateInput(attrs={'class':'with-border','type':'date'}))
    adult    = forms.IntegerField(min_value=1, initial=1,
                                  widget=forms.NumberInput(attrs={'class':'with-border'}))
    children = forms.IntegerField(min_value=0, initial=0,
                                  widget=forms.NumberInput(attrs={'class':'with-border'}))
