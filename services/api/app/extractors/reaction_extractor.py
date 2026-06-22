from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor
from app.extractors.schemas import ReactionExtractionOutput


class ReactionExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.REACTIONS.value
    schema_name = "reaction_extraction"
    output_model = ReactionExtractionOutput
    preferred_sections = ("Experimental", "Methods", "Supporting Information", "Results")
    max_chunks = 8
