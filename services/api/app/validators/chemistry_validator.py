from app.extractors.schemas import MeasurementType


MEASUREMENT_TYPES = set(MeasurementType.__args__)


def normalize_confidence(value: float | int | None) -> float | None:
    if value is None:
        return None
    return max(0.0, min(1.0, float(value)))


def validate_measurement_type(value: str) -> bool:
    return value in MEASUREMENT_TYPES
