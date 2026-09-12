
import requests
from datetime import date, timedelta


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _geocode(destination):
    """Resolve a city/place name to latitude and longitude using Open-Meteo."""
    response = requests.get(
        GEOCODING_URL,
        params={
            "name": destination,
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"Could not find a location for '{destination}'.")
    place = results[0]
    return (
        float(place["latitude"]),
        float(place["longitude"]),
        place.get("name", destination),
        place.get("country", ""),
    )


def get_weather(destination, duration, start_date=None):
    """
    Get a daily weather forecast for a trip.

    Returns the contract expected by itinerary_agent:
    [
      {
        "date": "YYYY-MM-DD",
        "condition": "Sunny",
        "temp_high": 28,
        "temp_low": 18,
        "precipitation_probability": 10
      }
    ]

    Open-Meteo is used because it does not require a separate API key.
    Forecast availability is limited to the provider's forecast horizon.
    """
    if start_date is None:
        start_date = date.today()
    elif hasattr(start_date, "date"):
        start_date = start_date.date()
    elif isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)

    duration = max(1, int(duration))

    lat, lon, place_name, country = _geocode(destination)

    # Open-Meteo provides a multi-day forecast. Request enough days for the trip.
    forecast_days = min(max(duration, 1), 16)

    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join([
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
            ]),
            "timezone": "auto",
            "forecast_days": forecast_days,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    rain = daily.get("precipitation_probability_max", [])

    code_map = {
        0: "Sunny",
        1: "Mainly Sunny",
        2: "Partly Cloudy",
        3: "Cloudy",
        45: "Foggy",
        48: "Foggy",
        51: "Light Drizzle",
        53: "Drizzle",
        55: "Heavy Drizzle",
        56: "Freezing Drizzle",
        57: "Heavy Freezing Drizzle",
        61: "Light Rain",
        63: "Rain",
        65: "Heavy Rain",
        66: "Freezing Rain",
        67: "Heavy Freezing Rain",
        71: "Light Snow",
        73: "Snow",
        75: "Heavy Snow",
        77: "Snow Grains",
        80: "Rain Showers",
        81: "Rain Showers",
        82: "Heavy Rain Showers",
        85: "Snow Showers",
        86: "Heavy Snow Showers",
        95: "Thunderstorm",
        96: "Thunderstorm + Hail",
        99: "Thunderstorm + Hail",
    }

    result = []
    for i in range(duration):
        target = start_date + timedelta(days=i)
        target_str = target.isoformat()

        if target_str in dates:
            idx = dates.index(target_str)
            result.append({
                "date": target_str,
                "condition": code_map.get(codes[idx], "Unknown"),
                "temp_high": highs[idx],
                "temp_low": lows[idx],
                "precipitation_probability": rain[idx],
            })
        else:
            # Keep the itinerary contract intact when the trip is outside
            # the available forecast horizon.
            result.append({
                "date": target_str,
                "condition": "Forecast unavailable",
                "temp_high": None,
                "temp_low": None,
                "precipitation_probability": None,
            })

    return result


if __name__ == "__main__":
    print(get_weather("Istanbul, Turkey", 4))
