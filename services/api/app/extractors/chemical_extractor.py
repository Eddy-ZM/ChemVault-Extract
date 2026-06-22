from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor
from app.extractors.schemas import ChemicalEntityExtractionOutput


class ChemicalEntityExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.CHEMICAL_ENTITIES.value
    schema_name = "chemical_entity_extraction"
    output_model = ChemicalEntityExtractionOutput
    preferred_sections = ("Experimental", "Methods", "Results", "Tables")
    max_chunks = 8
