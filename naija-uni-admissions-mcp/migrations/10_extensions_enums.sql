-- Campus Compass Knowledge Base Schema (CKAP)
-- Production tables + Staging layer + Knowledge Versioning + Storage linkage
-- Idempotent: safe to re-run in Supabase SQL Editor
-- Run this in Supabase SQL Editor

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ============================================================================
-- ENUMS (idempotent via DO blocks — CREATE TYPE has no IF NOT EXISTS)
-- ============================================================================
do $$ begin
    create type institution_type as enum (
        'university', 'polytechnic', 'college_of_education',
        'nursing_school', 'college_of_health_technology',
        'innovation_enterprise_institution', 'monotechnic'
    );
exception when duplicate_object then null; end $$;

do $$ begin
    create type ownership_type as enum ('federal', 'state', 'private');
exception when duplicate_object then null; end $$;

do $$ begin
    create type crawl_status as enum ('success', 'failed', 'partial', 'rate_limited');
exception when duplicate_object then null; end $$;

do $$ begin
    create type confidence_level as enum ('low', 'medium', 'high');
exception when duplicate_object then null; end $$;

do $$ begin
    create type validation_status as enum ('pending_review', 'approved', 'rejected', 'validated');
exception when duplicate_object then null; end $$;

do $$ begin
    create type document_type as enum (
        'webpage', 'pdf', 'official_bulletin', 'jamb_brochure',
        'news_article', 'screenshot', 'other'
    );
exception when duplicate_object then null; end $$;

do $$ begin
    create type degree_level as enum ('ND', 'HND', 'NCE', 'BSc', 'BA', 'BEng', 'BTech', 'BEd', 'MBBS', 'LLB', 'BPharm', 'BVSc', 'DVM', 'other');
exception when duplicate_object then null; end $$;

do $$ begin
    create type course_level as enum ('undergraduate', 'ND', 'HND', 'NCE', 'postgraduate');
exception when duplicate_object then null; end $$;
