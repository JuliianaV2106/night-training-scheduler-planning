"""
Mandatory Test Fixture: explain_assert
Helper that asserts a decision record or explanation carries >= 1 rule ID,
non-empty citations, and observed values.
"""

from typing import Any


def assert_explainability(
    record: dict[str, Any] | Any,
    expected_rule_id: str,
    required_keys: list[str] = None
) -> None:
    """
    Asserts that a decision record satisfies explainability criteria (AD-3, PRD §6.1).
    - Contains >= 1 cited rule ID.
    - Citations array is non-empty.
    - Required observed value keys exist.
    """
    if hasattr(record, "model_dump"):
        data = record.model_dump()
    elif isinstance(record, dict):
        data = record
    else:
        data = vars(record)

    citations = data.get("citations", [])
    if isinstance(citations, str):
        import json
        citations = json.loads(citations)

    assert len(citations) >= 1, f"Explainability violation: citations array is empty: {data}"
    assert any(expected_rule_id in c for c in citations), (
        f"Expected rule ID '{expected_rule_id}' not found in citations: {citations}"
    )

    if required_keys:
        inputs = data.get("inputs", {})
        if isinstance(inputs, str):
            import json
            inputs = json.loads(inputs)
        for key in required_keys:
            assert key in inputs or key in data, (
                f"Explainability violation: missing observed input key '{key}' in {data}"
            )
