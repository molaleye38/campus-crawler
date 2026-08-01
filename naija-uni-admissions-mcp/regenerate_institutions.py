#!/usr/bin/env python3
"""Regenerate institutions.py with enriched discovery data merged with existing seeds."""

import sys
from pathlib import Path
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from naija_admissions.models import InstitutionSeed, InstitutionType, OwnershipType

# Load existing seeds
from naija_admissions.institutions import ALL_INSTITUTIONS as EXISTING_SEEDS

# Load discovered data
from naija_admissions.discovery import run_discovery
import asyncio
import json

# Run discovery
results = asyncio.run(run_discovery(connectors=['nuc', 'ncce'], output_path=None))
print(f"Discovered {len(results)} institutions from regulatory sources")

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

# Build lookup of existing seeds by name
existing = {inst.name.lower().strip(): inst for inst in EXISTING_SEEDS}

# Merge discovered data into existing seeds
updated = 0
added_website = 0
for disc in results:
    best_match = None
    best_score = 0.85
    for name, seed in existing.items():
        score = similarity(name, disc.name)
        if score > best_score:
            best_score = score
            best_match = seed
    
    if best_match:
        if disc.website and not best_match.website:
            best_match.website = disc.website
            added_website += 1
            updated += 1
        if disc.year_established and not best_match.year_established:
            best_match.year_established = disc.year_established
            updated += 1
        if disc.state and not best_match.state:
            best_match.state = disc.state
            updated += 1

print(f"Matched and updated {updated} seeds, added {added_website} websites")
print(f"Remaining without website: {sum(1 for s in existing.values() if not s.website)}")

# Now write the complete regenerated institutions.py
out_path = Path(__file__).resolve().parent / "src" / "naija_admissions" / "institutions.py"

# Build all seeds as dicts
seeds_data = []
for inst in EXISTING_SEEDS:
    d = {
        'name': inst.name,
        'short_name': inst.short_name,
        'institution_type': inst.institution_type.value,
        'type': inst.type.value,
        'state': inst.state,
        'city': inst.city,
        'website': inst.website,
        'year_established': inst.year_established,
    }
    # Remove None values
    d = {k: v for k, v in d.items() if v is not None}
    seeds_data.append(d)

# Write the file
header = '''"""Seed list of Nigerian tertiary institutions.

Auto-generated from regulatory sources (NUC, NBTE, NCCE, NMCN, JAMB IBASS).
Do not edit manually - run discovery.py to refresh.
"""

from typing import Optional

from .models import InstitutionSeed, InstitutionType, OwnershipType


ALL_INSTITUTIONS: list[InstitutionSeed] = [
'''

lines = []
for seed in seeds_data:
    parts = []
    parts.append(f'    name="{seed["name"]}"')
    parts.append(f'    institution_type=InstitutionType.{seed["institution_type"].upper()}')
    parts.append(f'    type=OwnershipType.{seed["type"].upper()}')
    if seed.get('state'):
        parts.append(f'    state="{seed["state"]}"')
    if seed.get('city'):
        parts.append(f'    city="{seed["city"]}"')
    if seed.get('website'):
        parts.append(f'    website="{seed["website"]}"')
    if seed.get('year_established'):
        parts.append(f'    year_established={seed["year_established"]}')
    if seed.get('short_name'):
        parts.append(f'    short_name="{seed["short_name"]}"')
    lines.append('    InstitutionSeed(\n' + ',\n'.join(parts) + '\n    ),')

footer = '''
]


# Helper functions

def filter_by_type(inst_type: InstitutionType) -> list[InstitutionSeed]:
    """Filter seeds by institution type."""
    return [s for s in ALL_INSTITUTIONS if s.institution_type == inst_type]


def filter_by_ownership(ownership: OwnershipType) -> list[InstitutionSeed]:
    """Filter seeds by ownership type."""
    return [s for s in ALL_INSTITUTIONS if s.type == ownership]


def filter_by_state(state: str) -> list[InstitutionSeed]:
    """Filter seeds by state (case-insensitive)."""
    state_lower = state.lower()
    return [s for s in ALL_INSTITUTIONS if s.state and s.state.lower() == state_lower]


def seed_counts() -> dict[str, int]:
    """Return counts of institutions by type and ownership."""
    counts = {
        'total': len(ALL_INSTITUTIONS),
        'by_type': {},
        'by_ownership': {},
        'by_state': {},
    }
    for s in ALL_INSTITUTIONS:
        t = s.institution_type.value
        counts['by_type'][t] = counts['by_type'].get(t, 0) + 1
        o = s.type.value
        counts['by_ownership'][o] = counts['by_ownership'].get(o, 0) + 1
        if s.state:
            counts['by_state'][s.state] = counts['by_state'].get(s.state, 0) + 1
    return counts
'''

output = header + '\n'.join(lines) + '\n]' + footer

out_path.write_text(output, encoding='utf-8')

print(f"Wrote {len(seeds_data)} seeds to {out_path}")
print("Done!")