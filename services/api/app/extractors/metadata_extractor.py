from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor


class MetadataExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.METADATA.value
    preferred_sections = ("Abstract", "Introduction")
    max_chunks = 4
