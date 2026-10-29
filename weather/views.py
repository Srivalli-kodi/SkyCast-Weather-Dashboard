import unicodedata
import os
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from .models import City
from .forms import CityForm


CURRENT_WEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)

FORECAST_URL = (
    "https://api.openweathermap.org/data/2.5/forecast"
)


def get_api_key():
    api_key = os.getenv("OPENWEATHER_API_KEY") or settings.OPENWEATHER_API_KEY

    if not api_key:
        raise ValueError(
            "OpenWeatherMap API key is missing."
        )

    return api_key


def get_weather_data(city_name):

    api_key = get_api_key()

    location = city_name.strip()
    params = {
    "q": location,
    "appid": api_key,
    "units": "metric",
}
    try:
        response = requests.get(
            CURRENT_WEATHER_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.HTTPError:

        if response.status_code == 404:
            raise ValueError("City not found.")

        raise ValueError(
            "Weather service returned an error."
        )

    except requests.exceptions.Timeout:
        raise ValueError(
            "Weather service took too long to respond."
        )

    except requests.exceptions.RequestException:
        raise ValueError(
            "Unable to connect to weather service."
        )


def get_forecast_data(city_name):

    api_key = get_api_key()

    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric",
    }

    try:

        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException:
        raise ValueError(
            "Unable to fetch forecast information."
        )

def remove_diacritics(text):
    if not text:
        return text

    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
def format_weather(data, city_id=None):

    return {
        "id": city_id,
        "city": remove_diacritics(data.get("name")),
        "country": data.get("sys", {}).get("country"),

        "temperature": round(
            data["main"]["temp"]
        ),

        "feels_like": round(
            data["main"]["feels_like"]
        ),

        "humidity": data["main"]["humidity"],

        "pressure": data["main"]["pressure"],

        "wind_speed": round(
            data.get("wind", {}).get("speed", 0) * 3.6,
            1,
        ),

        "description": (
            data["weather"][0]["description"].title()
        ),

        "icon": data["weather"][0]["icon"],

        "icon_url": (
            f"https://openweathermap.org/img/wn/"
            f"{data['weather'][0]['icon']}@2x.png"
        ),
    }

def format_forecast(data):

    forecast = []

    for item in data.get("list", []):

        forecast.append(
            {
                "datetime": item["dt_txt"],

                "temperature": round(
                    item["main"]["temp"]
                ),

                "feels_like": round(
                    item["main"]["feels_like"]
                ),

                "humidity": item["main"]["humidity"],

                "description": (
                    item["weather"][0]["description"].title()
                ),

                "icon_url": (
                    f"https://openweathermap.org/img/wn/"
                    f"{item['weather'][0]['icon']}@2x.png"
                ),
            }
        )

    return forecast


def index(request):

    form = CityForm()

    if request.method == "POST":

        form = CityForm(request.POST)

        if form.is_valid():

            city_name = form.cleaned_data["name"]

            if City.objects.filter(
                name__iexact=city_name
            ).exists():

                messages.warning(
                    request,
                    f"{city_name} is already saved."
                )

            else:

                try:

                    get_weather_data(city_name)

                    City.objects.create(
                        name=city_name
                    )

                    messages.success(
                        request,
                        f"{city_name} added successfully!"
                    )

                except ValueError as error:

                    messages.error(
                        request,
                        str(error)
                    )

            return redirect("home")

    cities = City.objects.all()

    weather_data = []

    for city in cities:

        try:

            data = get_weather_data(city.name)

            weather_data.append(
                format_weather(data,city.id)
            )

        except ValueError:
            continue

    context = {
        "form": form,
        "weather_data": weather_data,
    }

    return render(
        request,
        "weather/weather.html",
        context
    )


def forecast(request, city_name):

    try:

        data = get_forecast_data(city_name)

        current = get_weather_data(city_name)

        context = {
            "weather": format_weather(current),
            "forecast": format_forecast(data),
        }

        return render(
            request,
            "weather/forecast.html",
            context
        )

    except ValueError as error:

        messages.error(
            request,
            str(error)
        )

        return redirect("home")



def delete_city(request, city_id):
    city = get_object_or_404(City, id=city_id)
    city_name = city.name
    city.delete()

    messages.success(request, f"{city_name} removed successfully.")
    return redirect("home")
