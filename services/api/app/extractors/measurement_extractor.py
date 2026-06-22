from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor


class MeasurementExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.MEASUREMENTS.value
    preferred_sections = ("Experimental", "Results", "Tables", "Supporting Information")
    max_chunks = 8
