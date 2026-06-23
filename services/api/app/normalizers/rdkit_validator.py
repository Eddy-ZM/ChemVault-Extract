from __future__ import annotations

from app.normalizers.text_normalizer import normalize_whitespace

try:  # pragma: no cover - optional dependency
    from rdkit import Chem  # type: ignore

    _RDKIT_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Chem = None
    _RDKIT_AVAILABLE = False


def validate_smiles(smiles: str | None) -> tuple[bool | None, str | None, list[str]]:
    canonical = normalize_whitespace(smiles)
    if not canonical:
        return None, None, []

    if not _RDKIT_AVAILABLE:
        return None, canonical, ["rdkit_available=false"]

    try:
        molecule = Chem.MolFromSmiles(canonical) if Chem is not None else None
    except Exception as exc:  # pragma: no cover - defensive for optional dependency
        return False, canonical, [f"RDKit parse error: {exc}"]

    if molecule is None:
        return False, canonical, ["RDKit could not parse canonical SMILES."]

    return True, Chem.MolToSmiles(molecule), []  # type: ignore[union-attr]


def rdkit_status() -> str:
    return "available" if _RDKIT_AVAILABLE else "unavailable"
