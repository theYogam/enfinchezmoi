from django import forms


class SubmitAdForm(forms.Form):
    surface_hood = forms.IntegerField(error_messages={'required': 'Please enter the surface hood'}, required=False)
    bedroom_count = forms.IntegerField(required=False)
    bathroom_count = forms.IntegerField(required=False)
    kitchen_count = forms.IntegerField(required=False)
    saloon_count = forms.IntegerField(required=False)
    room_count = forms.IntegerField(required=False)
    has_ac = forms.BooleanField(required=False)
    has_parking = forms.BooleanField(required=False)
    has_safeguard = forms.BooleanField(required=False)
    has_cleaning_service = forms.BooleanField(required=False)
    is_furnished = forms.BooleanField(required=False)
    is_registered = forms.BooleanField(required=False)
    description = forms.TextInput()


class OwnerForm(forms.Form):
    phone = forms.CharField(error_messages={'required': 'Please enter your phone'}, required=True)
    email = forms.EmailField(error_messages={'required': 'Please enter your email'}, required=True)


