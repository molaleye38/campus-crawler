# Campus Crawler - Sprint Plan

## Overview
Knowledge Acquisition Platform (CKAP) - Crawl all 583 Nigerian tertiary institutions
Target: 100% coverage of admission-critical data

## Branch Strategy
- Base: `main`
- Each sub-sprint = feature branch from `main`
- After completion: PR to `main`, merge, tag

---

## Sprint 1 Sub-Branches (All from `main`)

### Sprint 1.1: URL Filtering Hardening
**Branch**: `sprint/1.1-url-filtering`
**File**: `naija-uni-admissions-mcp/src/naija_admissions/website_mapper.py`

### Sprint 1.2: HEAD Pre-Check
**Branch**: `sprint/1.2-head-check`
**File**: `naija-uni-admissions-mcp/src/naija_admissions/crawl4ai_client.py`

### Sprint 1.3: Scope Optimization (Priority Order)
**Branch**: `sprint/1.3-scope-optimization`
**File**: `naija-uni-admissions-mcp/src/naija_admissions/scraper.py`

### Sprint 1.4: Bulk Crawl Script
**Branch**: `sprint/1.4-bulk-crawl-script`
**New File**: `scripts/bulk_crawl_all.py`

### Sprint 1.5: Validate & Promote Script
**Branch**: `sprint/1.5-validate-promote`
**New File**: `scripts/validate_and_promote.py`

### Sprint 1.6: GitHub Actions Matrix
**Branch**: `sprint/1.6-gh-actions`
**New File**: `.github/workflows/bulk-crawl.yml`

### Sprint 1.7: Coverage Report
**Branch**: `sprint/1.7-coverage-report`
**New File**: `scripts/coverage_report.py`

---

## Sprint 2: KG Integration (campus-compass)
**Branch**: `sprint/2-kg-reader`
**Repo**: `campus-compass`

---

## Branch Management Rules

1. Each sub-sprint = PR to `main`
2. PR title: `[Sprint 1.X] Description`
3. After merge: delete branch, tag `v1.x.x`
4. Sprint completion = tag `v1.0.0` on `main`

---

## Sprint 1 Commands

```bash
# Create all sub-branches
cd campus-crawler
git checkout main
git pull origin main

# Sub-branches
git checkout -b sprint/1.1-url-filtering
git checkout -b sprint/1.2-head-check
git checkout -b sprint/1.3-scope-optimization
git checkout -b sprint/1.4-bulk-crawl-script
git checkout -b sprint/1.5-validate-promote
git checkout -b sprint/1.6-gh-actions
git checkout -b sprint/1.7-coverage-report

# Main sprint branch
git checkout -b sprint/1-bulk-crawl
```