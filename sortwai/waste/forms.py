from django import forms

from sortwai.waste.models import Municipality


class MunicipalityForm(forms.Form):
    municipality = forms.ChoiceField(choices=Municipality.get_municipality_choices)

class ImageForm(forms.Form):
    image = forms.ImageField()

