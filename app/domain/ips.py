from dataclasses import dataclass


@dataclass
class CoordinatesData:
    latitude: float
    longitude: float
    status: str = "OK"
