from app.constants import ExtractorType
from app.extractors.base import BaseStructuredExtractor


class ReactionExtractor(BaseStructuredExtractor):
    extractor_type = ExtractorType.REACTIONS.value
    preferred_sections = ("Experimental", "Methods", "Supporting Information", "Results")
    max_chunks = 8
