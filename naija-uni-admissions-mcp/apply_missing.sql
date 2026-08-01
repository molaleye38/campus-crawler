-- Migration: Apply 15 missing tables + 1 missing column to existing Supabase DB
-- Run this in Supabase SQL Editor

-- =====================================================
-- 1. Add missing column to existing admission_requirements
-- =====================================================
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS olevel_sittings_max integer DEFAULT 2;

-- =====================================================
-- 2. Create 15 missing tables
-- =====================================================

-- departments
create table if not exists departments (

    id uuid primary key default uuid_generate_v4(),
    faculty_id uuid not null references faculties(id) on delete cascade,
    institution_id uuid not null references institutions(id) on delete cascade,
    name text not null,
    short_name text,
    code text,
    created_at timestamptz not null default now(),
    unique(faculty_id, name)

);

-- courses
create table if not exists courses (

    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    department_id uuid references departments(id) on delete set null,
    faculty_id uuid references faculties(id) on delete set null,
    name text not null,
    degree degree_level,
    level course_level,
    duration_years integer,
    affiliated_university text,
    jamb_subject_combination text[],
    created_at timestamptz not null default now(),
    unique(institution_id, name)

);

-- course_aliases
create table if not exists course_aliases (

    id uuid primary key default uuid_generate_v4(),
    canonical_course_id uuid not null references courses(id) on delete cascade,
    alias text not null,
    alias_type text not null default 'abbreviation', -- abbreviation, former_name, common_name
    created_at timestamptz not null default now(),
    unique(canonical_course_id, alias)

);

-- subjects
create table if not exists subjects (

    id uuid primary key default uuid_generate_v4(),
    name text unique not null,
    code text unique,
    subject_category text, -- 'core', 'science', 'arts', 'commercial', 'language'
    created_at timestamptz not null default now()

);

-- subject_aliases
create table if not exists subject_aliases (

    id uuid primary key default uuid_generate_v4(),
    canonical_subject_id uuid not null references subjects(id) on delete cascade,
    alias text not null,
    created_at timestamptz not null default now(),
    unique(canonical_subject_id, alias)

);

-- olevel_requirements
create table if not exists olevel_requirements (

    id uuid primary key default uuid_generate_v4(),
    admission_requirement_id uuid not null references admission_requirements(id) on delete cascade,
    subject_id uuid not null references subjects(id) on delete cascade,
    is_required boolean default true,
    min_grade text default 'C6',
    notes text,
    created_at timestamptz not null default now(),
    unique(admission_requirement_id, subject_id)

);

-- utme_requirements
create table if not exists utme_requirements (

    id uuid primary key default uuid_generate_v4(),
    admission_requirement_id uuid not null references admission_requirements(id) on delete cascade,
    subject_id uuid not null references subjects(id) on delete cascade,
    is_required boolean default true,
    is_compulsory boolean default false, -- English is always compulsory
    notes text,
    created_at timestamptz not null default now(),
    unique(admission_requirement_id, subject_id)

);

-- direct_entry
create table if not exists direct_entry (

    id uuid primary key default uuid_generate_v4(),
    admission_requirement_id uuid not null references admission_requirements(id) on delete cascade,
    qualification_type text not null, -- 'A-Level', 'ND', 'HND', 'NCE', 'Degree', 'IJMB', 'JUPEB', 'Other'
    qualification_subject text,
    min_grade text,
    min_cgpa numeric(3,2),
    accepts_ijmb boolean default false,
    accepts_jupeb boolean default false,
    notes text,
    created_at timestamptz not null default now()

);

-- post_utme
create table if not exists post_utme (

    id uuid primary key default uuid_generate_v4(),
    admission_requirement_id uuid not null references admission_requirements(id) on delete cascade,
    required boolean default true,
    format text, -- 'examination', 'screening', 'aptitude_test', 'oral_interview'
    weight_pct integer,
    min_score integer,
    duration_minutes integer,
    subjects text[], -- which subjects are tested
    past_questions_url text,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(admission_requirement_id)

);

-- aggregate_formulas
create table if not exists aggregate_formulas (

    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    course_id uuid references courses(id) on delete cascade,
    formula_text text not null, -- e.g., '(UTME/8) + (POST_UTME/2)'
    formula_json jsonb, -- structured: {"utme_weight": 0.125, "post_utme_weight": 0.5, "olevel_weight": 0.375}
    effective_from text not null, -- academic session e.g. '2025/2026'
    effective_to text,
    is_default boolean default false,
    created_at timestamptz not null default now(),
    unique(institution_id, course_id, effective_from)

);

-- elds
create table if not exists elds (

    id uuid primary key default uuid_generate_v4(),
    state_name text unique not null,
    is_active boolean default true,
    jamb_session text, -- which JAMB session this list applies to
    notes text,
    created_at timestamptz not null default now()

);

-- fees
create table if not exists fees (

    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    course_id uuid references courses(id) on delete cascade,
    faculty_id uuid references faculties(id) on delete cascade,
    fee_category text not null, -- 'tuition', 'acceptance', 'application', 'hostel', 'lab', 'exam', 'other'
    amount_ngn integer not null,
    amount_usd integer,
    currency text default 'NGN',
    indigene_amount_ngn integer,
    non_indigene_amount_ngn integer,
    academic_session text not null,
    is_per_session boolean default true,
    payment_schedule text, -- 'full', 'per_semester', 'instalment'
    source_url text,
    notes text,
    created_at timestamptz not null default now(),
    unique(institution_id, course_id, faculty_id, fee_category, academic_session)

);

-- deadlines
create table if not exists deadlines (

    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    course_id uuid references courses(id) on delete cascade,
    deadline_type text not null, -- 'application_open', 'application_close', 'post_utme_reg_open', 'post_utme_reg_close', 'post_utme_exam', 'acceptance_fee', 'clearance', 'resumption'
    deadline_date date not null,
    academic_session text not null,
    is_extended boolean default false,
    extension_date date,
    source_url text,
    notes text,
    created_at timestamptz not null default now(),
    unique(institution_id, course_id, deadline_type, academic_session)

);

-- admission_news
create table if not exists admission_news (

    id uuid primary key default uuid_generate_v4(),
    institution_id uuid references institutions(id) on delete cascade,
    title text not null,
    content text,
    summary text,
    source_url text not null,
    published_date timestamptz,
    crawled_at timestamptz not null default now(),
    news_category text, -- 'admission_list', 'supplementary', 'deadline_extension', 'policy_change', 'general'
    is_critical boolean default false,
    content_hash text,
    unique(source_url, content_hash)

);

-- knowledge_versions
create table if not exists knowledge_versions (

    id uuid primary key default uuid_generate_v4(),
    table_name text not null, -- 'institutions', 'courses', 'departmental_cutoffs', etc.
    record_id uuid not null,
    institution_id uuid references institutions(id) on delete set null,
    version_number integer not null,
    effective_date timestamptz not null,
    previous_value jsonb,
    new_value jsonb not null,
    changed_fields text[],
    source_document_id uuid references source_documents(id) on delete set null,
    crawl_log_id uuid references crawl_logs(id) on delete set null,
    change_reason text, -- 'initial_crawl', 'update', 'correction', 'manual_override'
    created_by text default 'crawler',
    created_at timestamptz not null default now()

);

