from datetime import date

from fastapi import APIRouter, Query
from fastapi.exceptions import RequestValidationError

from app.core.errors.base import AppError
from app.services.external_apis.weather_api import WeatherAPI

router = APIRouter(prefix="/weather", tags=["weather"])

ALL_HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "rain",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "wind_direction_10m",
    "wind_speed_10m",
    "soil_temperature_0cm",
    "uv_index",
]


@router.get("/forecast")
def get_weather_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: date = Query(...),
    end_date: date = Query(...),
    fields: str | None = None,
):
    """
    Fetch hourly weather forecast data for the given coordinates and date range.

    Coordinates must be supplied as **decimal degrees** — not degree/minute/second notation. E.g. -122.4194, 37.7749.
    Dates must use the **YYYY-MM-DD** format (ISO 8601).
    """
    if end_date < start_date:
        raise RequestValidationError(
            errors=[
                {
                    "loc": ("query", "end_date"),
                    "msg": "end_date must not be before start_date",
                    "input": end_date.isoformat(),
                    "type": "value_error",
                }
            ]
        )

    weather_api = WeatherAPI()
    try:
        requested = [f.strip() for f in fields.split(",") if f.strip()] if fields else []
        weather_data = weather_api.get_weather(
            latitude, longitude, start_date.isoformat(), end_date.isoformat(), hourly_fields=requested
        )
        return weather_data
    except Exception as e:
        raise AppError(str(e), status_code=500)