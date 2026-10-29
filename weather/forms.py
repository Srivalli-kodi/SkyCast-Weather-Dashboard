from django import forms
from .models import City


class CityForm(forms.ModelForm):

    class Meta:
        model = City
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "input city-input",
                    "placeholder": "Enter only city name ",
                    "autocomplete": "off",
                }
            )
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError("Please enter a city name.")

        if len(name) < 2:
            raise forms.ValidationError(
                "City name must contain at least 2 characters."
            )

        return name.title()