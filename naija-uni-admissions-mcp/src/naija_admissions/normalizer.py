"""Light normalizer — name cleanup, source dedupe."""

from __future__ import annotations

from .models import Institution, InstitutionSeed, Source


def canonicalize_name(name: str) -> str:
    n = name.strip()
    n = n.replace(",", ", ")
    while "  " in n:
        n = n.replace("  ", " ")
    return n


def short_name_fallback(name: str) -> str | None:
    # Try to derive an acronym from major capitalized words.
    tokens = [t for t in name.split() if t and (t[0].isupper() or t.isupper())]
    if len(tokens) >= 2:
        acro = "".join(t[0] for t in tokens if t[0].isalpha())
        return acro[:8].upper() if len(acro) >= 2 else None
    return None


def merge_sources(*lists: list[Source]) -> list[Source]:
    seen: set[str] = set()
    out: list[Source] = []
    for lst in lists:
        for s in lst or []:
            if s.url in seen:
                continue
            seen.add(s.url)
            out.append(s)
    return out


def seed_to_institution(seed: InstitutionSeed) -> Institution:
    return Institution(
        institution_type=seed.institution_type,
        name=canonicalize_name(seed.name),
        short_name=seed.short_name or short_name_fallback(seed.name),
        type=seed.type,
        state=seed.state,
        city=seed.city,
        website=seed.website,
        year_established=seed.year_established,
    )
