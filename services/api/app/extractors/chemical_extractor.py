from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor


class ChemicalEntityExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.CHEMICAL_ENTITIES.value
    preferred_sections = ("Experimental", "Methods", "Results", "Tables")
    max_chunks = 8
