from pathlib import Path

import pytest

from app.extraction import extract_text
from app.llm import extract_contract_data
from app.models import FileType
from tests.fixtures.ground_truth import GROUND_TRUTH

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FILE_TYPE_BY_EXTENSION = {
    ".pdf": FileType.pdf,
    ".docx": FileType.docx,
}

@pytest.mark.llm
@pytest.mark.parametrize("filename", GROUND_TRUTH.keys())
def test_extraction_accuracy(filename):
    path = FIXTURES_DIR / filename
    file_bytes = path.read_bytes()
    file_type = FILE_TYPE_BY_EXTENSION[path.suffix]

    text = extract_text(file_bytes, file_type)
    result = extract_contract_data(text)
    expected = GROUND_TRUTH[filename]

    extracted_parties = {(p.name, p.role.lower()) for p in result.parties}
    expected_parties = {(p["name"], p["role"].lower()) for p in expected["parties"]}
    assert expected_parties.issubset(extracted_parties), (f"missing expected parties: {expected_parties - extracted_parties}")

    extracted_by_type = {c.type: c for c in result.clauses}
    for clause_type, expected_value in expected["clauses"].items():
        assert clause_type in extracted_by_type, f"missing expected clause type: {clause_type}"
        actual_value = extracted_by_type[clause_type].value.model_dump()
        for field, expected_field_value in expected_value.items():
            assert actual_value[field] == expected_field_value, (
                f"{filename} {clause_type}.{field}: "
                f"expected {expected_field_value}, got {actual_value[field]}"
            )

    assert "termination_clause" in extracted_by_type, "missing termination_clause"
    termination_text =(extracted_by_type["termination_clause"].value.text or "").lower()
    for keyword in expected["termination_keywords"]:
        assert keyword.lower() in termination_text, (f"{filename} termination_clause missing expected keyword: {keyword}")

    for absent_type in expected["absent_clause_types"]:
        assert absent_type not in extracted_by_type, (f"{filename} unexpectedly extracted {absent_type}")