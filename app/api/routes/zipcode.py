from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError

from app.core.errors.base import AppError
from app.services.external_apis.zipcode_api import ZipCodeAPI

router = APIRouter(prefix="/zipcode", tags=["zipcode"])


@router.get("/lookup-address")
def lookup_address(address: str):
    """
    Resolve a free-form address to one or more geographic locations including
    postal code, latitude, longitude, place name, state, county, and country.

    Returns a list of matching results ordered by relevance (most relevant first).
    Each result is guaranteed to include `latitude` and `longitude`; `postal_code`
    is present when the geocoding service can determine it for the given address.

    Example: 
        address = "1600 Amphitheatre Parkway, Mountain View, CA, US"
    """
    if not address.strip():
        raise RequestValidationError(
            errors=[
                {
                    "loc": ("query", "address"),
                    "msg": "address must not be blank",
                    "input": address,
                    "type": "value_error",
                }
            ]
        )

    zipcode_api = ZipCodeAPI()
    try:
        return zipcode_api.lookup_address(address)
    except TimeoutError as e:
        raise AppError(str(e), status_code=504, error_code="GEOCODING_TIMEOUT")
    except RuntimeError as e:
        # Nominatim answered with an error: the failure is upstream, not ours
        raise AppError(str(e), status_code=502, error_code="GEOCODING_FAILED")
    except Exception as e:
        raise AppError(str(e), status_code=500)

