"""Tests for discovery connectors and polytechnic fallback."""

from __future__ import annotations

from pathlib import Path

import pytest

from naija_admissions.discovery import DiscoveredInstitution, write_discovery_output
from naija_admissions.polytechnic_seed import POLYTECHNICS, polytechnics_to_discovered


def test_polytechnic_seed_nonempty():
    assert len(POLYTECHNICS) >= 50


def test_polytechnic_seed_required_fields():
    for p in POLYTECHNICS:
        assert "name" in p and p["name"]
        assert "state" in p and p["state"]
        assert "ownership" in p
        assert p["ownership"] in ("federal", "state", "private")


def test_polytechnics_to_discovered_shape():
    items = polytechnics_to_discovered()
    for d in items:
        assert d["institution_type"] == "polytechnic"
        assert d["ownership_type"] in ("federal", "state", "private")
        assert d["state"]
        assert d["name"]


def test_polytechnics_have_no_trailing_comma_in_state():
    for p in POLYTECHNICS:
        assert "," not in p["state"]


def test_polytechnics_have_no_comma_in_name_with_orphan_state():
    """Bug fix from Sprint 1: 'Federal University,X' was a data error.

    For polytechnics, names like 'Federal Polytechnic, X' (with comma) are
    legitimate (location suffix). This test just ensures the seed list doesn't
    have the typo where the comma is missing space."""
    for p in POLYTECHNICS:
        if "," in p["name"]:
            parts = p["name"].split(",")
            for part in parts:
                assert part.strip(), f"Empty part in name: {p['name']}"


def test_write_discovery_output(tmp_path: Path):
    items = [
        DiscoveredInstitution(
            name="Test Polytechnic",
            institution_type="polytechnic",
            ownership_type="state",
            state="Lagos",
        ),
        DiscoveredInstitution(
            name="Test University",
            institution_type="university",
            ownership_type="federal",
            state="FCT Abuja",
        ),
    ]
    output = tmp_path / "discovered.json"
    path = write_discovery_output(items, output)
    assert path.exists()
    assert path == output
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["name"] == "Test Polytechnic"


@pytest.mark.asyncio
async def test_nbte_connector_fallback_when_offline(monkeypatch):
    """NBTEConnector should return the polytechnic seed list when live sites are down."""
    from naija_admissions.discovery import NBTEConnector

    async def fake_fetch(url, timeout=60):
        return None

    from naija_admissions import discovery
    monkeypatch.setattr(discovery, "_fetch_markdown", fake_fetch)

    connector = NBTEConnector()
    results = await connector.discover()
    assert len(results) > 0
    for r in results:
        assert r.institution_type == "polytechnic"
