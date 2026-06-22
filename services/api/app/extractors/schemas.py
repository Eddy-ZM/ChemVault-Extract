import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictExtractionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(StrictExtractionModel):
    document_id: str
    chunk_id: str
    page: int | None
    section: str | None
    quote: str


class PaperMetadata(StrictExtractionModel):
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    keywords: list[str] = Field(default_factory=list)
    evidence: Evidence | None = None


ChemicalRole = Literal[
    "reactant",
    "product",
    "reagent",
    "solvent",
    "catalyst",
    "analyte",
    "standard",
    "unknown",
]


class ChemicalObject(StrictExtractionModel):
    name: str | None = None
    role: ChemicalRole = "unknown"
    formula: str | None = None
    smiles: str | None = None
    inchi: str | None = None
    cas: str | None = None
    amount: str | None = None
    unit: str | None = None
    context: str | None = None


class ChemicalEntityExtraction(ChemicalObject):
    name: str
    evidence: Evidence
    confidence: float | None = None


class ReactionExtraction(StrictExtractionModel):
    reaction_name: str | None = None
    reactants: list[ChemicalObject] = Field(default_factory=list)
    products: list[ChemicalObject] = Field(default_factory=list)
    reagents: list[ChemicalObject] = Field(default_factory=list)
    solvents: list[ChemicalObject] = Field(default_factory=list)
    catalysts: list[ChemicalObject] = Field(default_factory=list)
    temperature: str | None = None
    time: str | None = None
    atmosphere: str | None = None
    yield_value: str | None = None
    yield_unit: str | None = None
    procedure: str | None = None
    evidence: Evidence
    confidence: float | None = None


MeasurementType = Literal[
    "1H NMR",
    "13C NMR",
    "IR",
    "MS",
    "HRMS",
    "HPLC",
    "GCMS",
    "UV-vis",
    "melting_point",
    "boiling_point",
    "retention_time",
    "absorbance",
    "pKa",
    "yield",
    "mass",
    "volume",
    "concentration",
    "temperature",
    "time",
    "other",
]


class MeasurementCondition(StrictExtractionModel):
    name: str
    value: str | None = None
    unit: str | None = None


class MeasurementExtraction(StrictExtractionModel):
    target: str | None = None
    measurement_type: MeasurementType
    value: str | None = None
    unit: str | None = None
    conditions: list[MeasurementCondition] = Field(default_factory=list)
    raw_text: str
    evidence: Evidence
    confidence: float | None = None

    @field_validator("conditions", mode="before")
    @classmethod
    def normalize_conditions(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, dict):
            return [
                {
                    "name": str(condition_name),
                    "value": _condition_value_to_string(condition_value),
                    "unit": None,
                }
                for condition_name, condition_value in value.items()
            ]
        return value


class MetadataExtractionOutput(StrictExtractionModel):
    items: list[PaperMetadata] = Field(default_factory=list)


class ChemicalEntityExtractionOutput(StrictExtractionModel):
    items: list[ChemicalEntityExtraction] = Field(default_factory=list)


class ReactionExtractionOutput(StrictExtractionModel):
    items: list[ReactionExtraction] = Field(default_factory=list)


class MeasurementExtractionOutput(StrictExtractionModel):
    items: list[MeasurementExtraction] = Field(default_factory=list)


def _condition_value_to_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True)
