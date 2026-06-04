from django import forms
from .models import RoomService

class RoomServiceForm(forms.ModelForm):
    class Meta:
        model  = RoomService
        fields = ['service_type','description','price']
        widgets = {
            'service_type': forms.Select(attrs={'class':'with-border'}),
            'description':  forms.TextInput(attrs={'class':'with-border','placeholder':'Description'}),
            'price':        forms.NumberInput(attrs={'class':'with-border','placeholder':'0.00'}),
        }
