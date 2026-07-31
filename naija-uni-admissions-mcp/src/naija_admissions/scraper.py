"""Per-institution scraper — orchestrates search → scrape → parse → merge → upsert to Supabase."""

from __future__ import annotations

from typing import Any

from .ai_extractor import extract_with_nvidia
from .crawl4ai_client import Crawl4AIClient, SearchHit
from .extraction_models import ExtractedKnowledge
from .models import (
    AdmissionRequirements,
    ApplicationProcess,
    CatchmentArea,
    FeeTier,
    Institution,
    InstitutionType,
    Program,
    Source,
)
from .normalizer import merge_sources, seed_to_institution
from .parsers.catchment_parser import parse_catchment
from .parsers.fees_parser import parse_application_process, parse_fees
from .parsers.programs_parser import parse_programs
from .parsers.requirements_parser import parse_requirements
from .utils import polite_delay, safe_log
from .website_mapper import (
    SiteMap,
    filter_urls_for_scraping,
    map_institution_website,
)
try:
    from .storage import store_crawl_artifacts
except ImportError:
    store_crawl_artifacts = None

SUPABASE_ENABLED = True
AI_EXTRACTION_ENABLED = False  # Toggle for AI vs regex-only mode
WEBSITE_MAPPER_ENABLED = True  # Toggle for Phase 3 website mapper


def _queries_for(seed) -> list[tuple[str, list[str] | None]]:
    name = seed.name
    if seed.institution_type == InstitutionType.UNIVERSITY:
        return [
            (f"{name} admission requirements UTME Post-UTME direct entry catchment", None),
            (f"{name} admission application portal fees tuition indigene school fees", None),
        ]
    if seed.institution_type == InstitutionType.POLYTECHNIC:
        return [
            (f"{name} admission requirements ND cut-off mark JAMB", None),
            (f"{name} school fees tuition application portal admission", None),
        ]
    return [
        (f"{name} admission requirements NCE cut-off mark JAMB", None),
        (f"{name} school fees application portal admission NCE", None),
    ]


def _pick_urls(hits: list[SearchHit], seed, max_urls: int = 4) -> list[str]:
    if not hits:
        return []
    name_tokens = [t.lower() for t in seed.name.split() if len(t) > 3]
    site_token: str | None = None
    if seed.website:
        site_token = seed.website.replace("https://", "").replace("http://", "").split("/")[0].lower()

    scored: list[tuple[int, str]] = []
    for h in hits:
        url_l = h.url.lower()
        sc = 0
        if site_token and site_token in url_l:
            sc += 100
        for tok in name_tokens:
            if tok in url_l:
                sc += 10
        if "jamb.gov.ng" in url_l:
            sc += 30
        if "nuc.edu.ng" in url_l or "nbte.gov.ng" in url_l or "ncceonline" in url_l:
            sc += 25
        if "schoolnewsng" in url_l or "infoledge" in url_l or "myschoolgist" in url_l:
            sc += 5
        if any(b in url_l for b in ["facebook.com", "twitter.com", "x.com", "reddit.com"]):
            sc -= 50
        blob = ((h.title or "") + " " + (h.snippet or "")).lower()
        if "admission" in blob:
            sc += 5
        if "cut-off" in blob or "cutoff" in blob or "requirements" in blob:
            sc += 5
        scored.append((sc, h.url))

    scored.sort(reverse=True)
    seen: set[str] = set()
    out: list[str] = []
    for _, url in scored:
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
        if len(out) >= max_urls:
            break
    return out


def _apply_extracted_knowledge(inst: Institution, extracted: ExtractedKnowledge, seed) -> None:
    """Apply AI-extracted knowledge to Institution model, filling gaps with regex parsers."""
    from .models import (
        AdmissionRequirements,
        ApplicationProcess,
        CatchmentArea,
        CutoffEntry,
        FeeTier,
        PostUTME,
        Program,
    )
    
    # Institution basics (already set from seed, but AI might have better info)
    if extracted.institution and not inst.short_name:
        inst.short_name = extracted.institution.short_name
    if extracted.institution and not inst.website:
        inst.website = extracted.institution.website
    
    # ===== ADMISSION REQUIREMENTS =====
    ai_req = None
    if extracted.admission_requirements:
        # Take the first institution-level requirement (course_name is None)
        inst_level_req = next((r for r in extracted.admission_requirements if r.course_name is None), 
                              extracted.admission_requirements[0])
        
        # Build O-Level subjects from extracted olevel_requirements
        olevel_subjects = []
        if extracted.olevel_requirements:
            for ol in extracted.olevel_requirements:
                if ol.admission_req_course is None or ol.admission_req_course == inst_level_req.course_name:
                    olevel_subjects.append(ol.subject_name)
        
        # Build UTME subjects from extracted utme_requirements
        utme_subjects = []
        if extracted.utme_requirements:
            for utme in extracted.utme_requirements:
                if utme.admission_req_course is None or utme.admission_req_course == inst_level_req.course_name:
                    utme_subjects.append(utme.subject_name)
        
        # Per-course cutoffs from departmental_cutoffs
        per_course_cutoffs = []
        if extracted.departmental_cutoffs:
            for c in extracted.departmental_cutoffs:
                if c.merit_cutoff:
                    per_course_cutoffs.append({"course": c.course_name, "cutoff": int(c.merit_cutoff)})
        
        # Post-UTME
        post_utme = None
        if inst_level_req.post_utme_required is not None:
            post_utme = PostUTME(
                required=inst_level_req.post_utme_required,
                format=inst_level_req.post_utme_format.value if inst_level_req.post_utme_format else None,
                weight_pct=inst_level_req.post_utme_weight_pct,
            )
        
        ai_req = AdmissionRequirements(
            olevel_subjects=olevel_subjects or [],
            olevel_credits_min=inst_level_req.olevel_credits_min,
            utme_subjects=utme_subjects or [],
            utme_cutoff_general=inst_level_req.minimum_jamb,
            utme_cutoff_per_course=[
                CutoffEntry(course=c["course"], cutoff=c["cutoff"])
                for c in per_course_cutoffs
            ] if per_course_cutoffs else None,
            post_utme=post_utme,
            direct_entry_requirements=inst_level_req.direct_entry_requirements,
        )
    
    # Fallback to regex if AI didn't produce requirements
    if ai_req is None:
        try:
            inst.admission_requirements = parse_requirements(
                "\n\n".join(inst.raw_chunks if hasattr(inst, 'raw_chunks') else []), 
                seed.institution_type
            )
        except Exception as e:
            safe_log("requirements_parse_error", error=str(e), name=seed.name)
    else:
        inst.admission_requirements = ai_req
    
    # ===== APPLICATION PROCESS =====
    # (No direct AI extraction for this yet; fallback to regex)
    try:
        app_proc_dict = parse_application_process("\n\n".join(inst.raw_chunks if hasattr(inst, 'raw_chunks') else []))
        if app_proc_dict:
            inst.application_process = ApplicationProcess(**app_proc_dict)
    except Exception as e:
        safe_log("application_parse_error", error=str(e), name=seed.name)
    
    # ===== CATCHMENT =====
    if extracted.catchment:
        inst.catchment_areas = [
            CatchmentArea(
                name=c.name,
                details=c.details,
                policy=c.policy.value if c.policy else None,
            ) for c in extracted.catchment
        ]
    else:
        try:
            inst.catchment_areas = parse_catchment(
                "\n\n".join(inst.raw_chunks if hasattr(inst, 'raw_chunks') else []),
                seed.institution_type, seed.type.value, seed.state
            )
        except Exception as e:
            safe_log("catchment_parse_error", error=str(e), name=seed.name)
    
    # ===== PROGRAMS & FACULTIES =====
    if extracted.courses:
        # Faculties from extracted faculties
        if extracted.faculties:
            inst.faculties = list(set(f.name for f in extracted.faculties))
        else:
            # Derive from courses
            inst.faculties = list(set(c.faculty_name for c in extracted.courses if c.faculty_name))
        
        inst.programs = [
            Program(
                name=c.name,
                faculty=c.faculty_name,
                degree=c.degree.value if c.degree else None,
                level=c.level.value if c.level else None,
                duration_years=c.duration_years,
                affiliated_university=c.affiliated_university,
            ) for c in extracted.courses
        ]
    else:
        try:
            inst.faculties, inst.programs = parse_programs(
                "\n\n".join(inst.raw_chunks if hasattr(inst, 'raw_chunks') else []),
                seed.institution_type
            )
        except Exception as e:
            safe_log("programs_parse_error", error=str(e), name=seed.name)
    
    # ===== FEES =====
    if extracted.fees:
        inst.fee_tiers = []
        for f in extracted.fees:
            try:
                # Extract year from academic_session like "2025/2026" -> 2025
                fee_year = None
                if f.academic_session:
                    import re as _re
                    ym = _re.search(r"(20\d{2})", f.academic_session)
                    if ym:
                        fee_year = int(ym.group(1))
                
                fee = FeeTier(
                    program_or_faculty=f.course_name or f.faculty_name or "General",
                    tuition_per_session_ngn=f.amount_ngn,
                    tuition_per_session_usd=f.amount_usd,
                    currency=f.currency or "NGN",
                    indigene_vs_non_indigene=(
                        {"indigene": f.indigene_amount_ngn, "non_indigene": f.non_indigene_amount_ngn}
                        if f.indigene_amount_ngn and f.non_indigene_amount_ngn
                        else None
                    ),
                    source_url=f.source_url or extracted.institution.source_url or "unknown",
                    fee_year=fee_year,
                )
                inst.fee_tiers.append(fee)
            except Exception as e:
                safe_log("fee_tier_error", error=str(e), fee_category=f.fee_category.value if f.fee_category else "unknown")
    else:
        # Regex fallback
        try:
            fees = []
            for chunk in (inst.raw_chunks if hasattr(inst, 'raw_chunks') else []):
                try:
                    t = parse_fees(chunk, "")
                    if t:
                        fees.extend(t)
                except Exception:
                    continue
            seen_fees: set[tuple[str, int | None]] = set()
            unique_fees: list[FeeTier] = []
            for f in fees:
                key = (f.program_or_faculty, f.tuition_per_session_ngn)
                if key in seen_fees:
                    continue
                seen_fees.add(key)
                unique_fees.append(f)
            inst.fee_tiers = unique_fees
        except Exception:
            pass
    
    # ===== CUTOFFS =====
    if extracted.departmental_cutoffs:
        # Store in admission_requirements.utme_cutoff_per_course
        if inst.admission_requirements:
            inst.admission_requirements.utme_cutoff_per_course = [
                CutoffEntry(course=c.course_name, cutoff=int(c.merit_cutoff or 0))
                for c in extracted.departmental_cutoffs if c.merit_cutoff
            ]
            # Also set general if available
            if not inst.admission_requirements.utme_cutoff_general:
                general = [c for c in extracted.departmental_cutoffs if "general" in c.course_name.lower()]
                if general:
                    inst.admission_requirements.utme_cutoff_general = int(general[0].merit_cutoff or 0)


async def scrape_one(
    seed,
    client: Crawl4AIClient,
    on_credits_used,
) -> Institution:
    inst = seed_to_institution(seed)
    
    # Store raw chunks on the instance for fallback parsing
    inst.raw_chunks = []

    # ===== PHASE 3: WEBSITE MAPPER FOR TARGETED URL DISCOVERY =====
    target_urls: list[str] = []
    site_map: SiteMap | None = None
    
    if WEBSITE_MAPPER_ENABLED and seed.website:
        try:
            safe_log("mapper_start", name=seed.name, website=seed.website)
            site_map = await map_institution_website(
                seed=seed,
                client=client,
                max_depth=2,
                max_pages_per_category=4,
                max_total_pages=15,
            )
            target_urls = filter_urls_for_scraping(site_map, max_urls=12)
            safe_log("mapper_complete", name=seed.name, discovered=len(site_map.discovered_urls), selected=len(target_urls))
        except Exception as e:
            safe_log("mapper_failed", name=seed.name, error=str(e))
            target_urls = []
    
    # ===== FALLBACK: DDG SEARCH IF MAPPER DISABLED OR NO URLS FOUND =====
    if not target_urls:
        safe_log("mapper_fallback_to_ddg", name=seed.name)
        queries = _queries_for(seed)
        all_hits: list[SearchHit] = []
        for q, domains in queries:
            try:
                hits = await client.search(q, limit=5, include_domains=domains)
                all_hits.extend(hits)
            except Exception as e:
                safe_log("search_error", query=q, error=str(e), name=seed.name)
            await polite_delay()
        
        target_urls = _pick_urls(all_hits, seed, max_urls=8)
        
        # Also scrape search result contents for context
        raw_chunks: list[str] = []
        sources: list[Source] = []
        seen_urls: set[str] = set()
        for hit in all_hits[:8]:
            if hit.url in seen_urls:
                continue
            seen_urls.add(hit.url)
            if hit.content:
                raw_chunks.append(hit.content)
                sources.append(Source(url=hit.url))
    else:
        # Use website mapper URLs - scrape them
        raw_chunks = []
        sources = []
        seen_urls = set()
    
    safe_log("picked_urls", name=seed.name, urls=target_urls)

    for url in target_urls:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        await polite_delay()
        try:
            md = await client.scrape(url)
            if md:
                raw_chunks.append(md)
            sources.append(Source(url=url))
        except Exception as e:
            safe_log("scrape_error", url=url, error=str(e), name=seed.name)

    if not raw_chunks:
        inst.sources = sources
        inst.compute_confidence()
        return inst

    # Store raw chunks for fallback parsing
    inst.raw_chunks = raw_chunks
    combined = "\n\n".join(raw_chunks)

    # ===== AI EXTRACTION (PRIMARY) =====
    extracted: ExtractedKnowledge | None = None
    if AI_EXTRACTION_ENABLED:
        try:
            extracted = await extract_with_nvidia(
                markdown=combined,
                source_url=sources[0].url if sources else (seed.website or ""),
                institution_type=seed.institution_type.value,
            )
            safe_log("ai_extraction_success", name=seed.name, confidence=extracted.extraction_confidence.value if extracted.extraction_confidence else "unknown")
        except Exception as e:
            safe_log("ai_extraction_failed", error=str(e), name=seed.name)
            extracted = None

    # ===== APPLY EXTRACTED KNOWLEDGE + REGEX FALLBACK =====
    if extracted:
        _apply_extracted_knowledge(inst, extracted, seed)
    else:
        # Full regex fallback
        req: AdmissionRequirements | None = None
        try:
            req = parse_requirements(combined, seed.institution_type)
        except Exception as e:
            safe_log("requirements_parse_error", error=str(e), name=seed.name)
        inst.admission_requirements = req

        fees: list[FeeTier] = []
        for chunk, source in zip(raw_chunks, sources, strict=False):
            try:
                t = parse_fees(chunk, source.url)
                if t:
                    fees.extend(t)
            except Exception:
                continue
        seen_fees: set[tuple[str, int | None]] = set()
        unique_fees: list[FeeTier] = []
        for f in fees:
            key = (f.program_or_faculty, f.tuition_per_session_ngn)
            if key in seen_fees:
                continue
            seen_fees.add(key)
            unique_fees.append(f)
        inst.fee_tiers = unique_fees

        app_proc_dict: dict[str, Any] | None = None
        try:
            app_proc_dict = parse_application_process(combined)
        except Exception as e:
            safe_log("application_parse_error", error=str(e), name=seed.name)
        if app_proc_dict:
            inst.application_process = ApplicationProcess(**app_proc_dict)

        catchment: list[CatchmentArea] = []
        try:
            catchment = parse_catchment(combined, seed.institution_type, seed.type.value, seed.state)
        except Exception as e:
            safe_log("catchment_parse_error", error=str(e), name=seed.name)
        inst.catchment_areas = catchment

        faculties: list[str] = []
        programs: list[Program] = []
        try:
            faculties, programs = parse_programs(combined, seed.institution_type)
        except Exception as e:
            safe_log("programs_parse_error", error=str(e), name=seed.name)
        inst.faculties = faculties
        inst.programs = programs

    # If website not already captured and we found a credible one, grab it
    if not inst.website:
        for s in sources:
            if "jamb.gov.ng" in s.url:
                continue
            if any(tok in s.url.lower() for tok in seed.name.lower().split()) and "edunig" in s.url.lower() or seed.state in s.url:
                pass

    inst.sources = merge_sources(sources, [])
    
    # Store crawl artifacts in Supabase Storage (Sprint A — wired)
    if store_crawl_artifacts and SUPABASE_ENABLED:
        try:
            session_str = (getattr(seed, 'academic_session', None) or '2025/2026')
            artifacts = store_crawl_artifacts(
                institution_name=seed.name,
                academic_session=session_str,
                source_url=sources[0].url if sources else (seed.website or ''),
                html_content=raw_chunks[0].encode('utf-8') if raw_chunks else None,
                markdown_content=combined.encode('utf-8'),
            )
            safe_log("storage_artifacts_stored", name=seed.name, artifacts=list(artifacts.keys()))
        except Exception as e:
            safe_log("storage_artifacts_failed", name=seed.name, error=str(e))
    
    inst.compute_confidence()
    return inst