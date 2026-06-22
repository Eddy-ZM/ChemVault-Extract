from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor
from app.extractors.schemas import MeasurementExtractionOutput


class MeasurementExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.MEASUREMENTS.value
    schema_name = "measurement_extraction"
    output_model = MeasurementExtractionOutput
    preferred_sections = ("Experimental", "Results", "Tables", "Supporting Information")
    max_chunks = 8
