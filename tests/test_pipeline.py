"""Tests for the dlt pipeline source structure.

These tests verify the source's shape (resources defined, names correct)
without making any API calls — the FootballDataClient is mocked.
"""

from unittest.mock import MagicMock

from pl_platform.pipeline import football_data_source


def test_source_returns_expected_resources():
    """football_data_source should yield exactly 4 resources with expected names."""
    mock_client = MagicMock()
    source = football_data_source(mock_client)

    expected_names = {"competitions", "teams", "matches", "scorers"}
    actual_names = set(source.resources.keys())

    assert actual_names == expected_names, (
        f"Expected resources {expected_names}, got {actual_names}"
    )


def test_matches_uses_merge_disposition():
    """Matches needs merge for upsert-on-id semantics; others use replace."""
    mock_client = MagicMock()
    source = football_data_source(mock_client)

    # Matches is the only resource that should use merge
    assert source.resources["matches"].write_disposition == "merge"

    # The rest should use replace
    for name in ["competitions", "teams", "scorers"]:
        assert source.resources[name].write_disposition == "replace", (
            f"Expected {name} to use replace, got {source.resources[name].write_disposition}"
        )
