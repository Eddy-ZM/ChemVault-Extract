from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor
from app.extractors.schemas import MetadataExtractionOutput


class MetadataExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.METADATA.value
    schema_name = "metadata_extraction"
    output_model = MetadataExtractionOutput
    preferred_sections = ("Abstract", "Introduction")
    max_chunks = 4
