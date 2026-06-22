import re

SECTION_ALIASES = {
    "abstract": "Abstract",
    "introduction": "Introduction",
    "background": "Background",
    "experimental": "Experimental",
    "experimental section": "Experimental",
    "materials and methods": "Materials and Methods",
    "materials & methods": "Materials and Methods",
    "material and methods": "Materials and Methods",
    "methods": "Methods",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
    "conclusions": "Conclusion",
    "supporting information": "Supporting Information",
    "supplementary information": "Supporting Information",
    "si": "Supporting Information",
    "references": "References",
    "reference": "References",
    "appendix": "Appendix",
    "appendices": "Appendix",
}


def normalize_heading(text: str) -> str:
    cleaned = re.sub(r"^\s*\d+(\.\d+)*\.?\s+", "", text)
    cleaned = cleaned.strip().strip("#").strip().strip(":")
    cleaned = cleaned.replace("&", " & ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.casefold()


def detect_section(text: str | None) -> str | None:
    if not text:
        return None
    normalized = normalize_heading(text)
    if normalized in SECTION_ALIASES:
        return SECTION_ALIASES[normalized]
    return None
