from django import forms

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=300,
        widget=forms.TextInput(attrs={'class':'with-border','placeholder':'Full Name'}))
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class':'with-border','placeholder':'Email Address'}))
    phone = forms.CharField(required=False, max_length=30,
        widget=forms.TextInput(attrs={'class':'with-border','placeholder':'Phone Number'}))

class CouponForm(forms.Form):
    code = forms.CharField(max_length=100,
        widget=forms.TextInput(attrs={'class':'with-border','placeholder':'Coupon Code'}))
