from django import forms
from .models import Report

class ReportForm(forms.ModelForm):
    class Meta:
        model  = Report
        fields = ['title','report_type','data_from','data_to','notes']
        widgets = {
            'title':       forms.TextInput(attrs={'class':'with-border'}),
            'report_type': forms.Select(attrs={'class':'with-border'}),
            'data_from':   forms.DateInput(attrs={'class':'with-border','type':'date'}),
            'data_to':     forms.DateInput(attrs={'class':'with-border','type':'date'}),
            'notes':       forms.Textarea(attrs={'class':'with-border','rows':3}),
        }
