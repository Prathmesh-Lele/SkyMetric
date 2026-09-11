"""CPI comparison API endpoints.

Provides real Consumer Price Index data from MoSPI e-Sankhyiki
for comparison with SkyMetric airfare index.
"""

from fastapi import APIRouter

from skymetric.data.cpi_data import get_all_cpi_data, fetch_cpi_air_transport, fetch_cpi_general

router = APIRouter()


@router.get("/")
def get_cpi_comparison():
    """Get CPI data for comparison with SkyMetric airfare index.

    Returns real MoSPI CPI data including:
    - CPI General (All India)
    - CPI Transport division
    - CPI Passenger transport by air (class 07.3.3)
    """
    return get_all_cpi_data()


@router.get("/air-transport")
def get_cpi_air_transport():
    """Get CPI Air Transport index only (class 07.3.3)."""
    data = fetch_cpi_air_transport()
    return {
        "series": "CPI Air Transport (2024=100)",
        "data": data,
        "source": "MoSPI e-Sankhyiki",
        "class_code": "07.3.3",
        "note": "Official MoSPI CPI for passenger air transport. Base year 2024=100.",
    }


@router.get("/general")
def get_cpi_general():
    """Get CPI General index only."""
    data = fetch_cpi_general()
    return {
        "series": "CPI General (2024=100)",
        "data": data,
        "source": "MoSPI e-Sankhyiki",
        "note": "All India Combined CPI. Base year 2024=100.",
    }
