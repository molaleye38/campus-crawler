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

-- ============================================================================
-- PRODUCTION TABLES (22 tables per CKAP spec)
-- ============================================================================

-- 1. Institutions: one row per school
create table if not exists institutions (
    id uuid primary key default uuid_generate_v4(),
    name text unique not null,
    short_name text,
    institution_type institution_type not null,
    ownership_type ownership_type not null,
    state text,
    city text,
    website text,
    admission_portal text,
    year_established integer,
    jamb_code text,
    contact_email text,
    phone text,
    address text,
    accreditation_body text,
    last_updated timestamptz not null default now(),
    created_at timestamptz not null default now()
);

-- 2. Faculties within institutions
create table if not exists faculties (
    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    name text not null,
    short_name text,
    created_at timestamptz not null default now(),
    unique(institution_id, name)
);

-- 3. Departments within faculties
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

-- 4. Courses/Programs (the actual study programmes)
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

-- 5. Course aliases (UNILAG → University of Lagos, Comp Sci → Computer Science)
create table if not exists course_aliases (
    id uuid primary key default uuid_generate_v4(),
    canonical_course_id uuid not null references courses(id) on delete cascade,
    alias text not null,
    alias_type text not null default 'abbreviation', -- abbreviation, former_name, common_name
    created_at timestamptz not null default now(),
    unique(canonical_course_id, alias)
);

-- 6. Subjects (O-Level / UTME)
create table if not exists subjects (
    id uuid primary key default uuid_generate_v4(),
    name text unique not null,
    code text unique,
    subject_category text, -- 'core', 'science', 'arts', 'commercial', 'language'
    created_at timestamptz not null default now()
);

-- 7. Subject aliases (English → English Language, Maths → Mathematics)
create table if not exists subject_aliases (
    id uuid primary key default uuid_generate_v4(),
    canonical_subject_id uuid not null references subjects(id) on delete cascade,
    alias text not null,
    created_at timestamptz not null default now(),
    unique(canonical_subject_id, alias)
);

-- 8. Admission requirements (institution-level or course-level)
create table if not exists admission_requirements (
    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    course_id uuid references courses(id) on delete cascade,
    olevel_credits_min integer,
    olevel_sittings_max integer default 2,
    awaiting_result_accepted boolean default true,
    direct_entry_requirements text,
    minimum_jamb integer,
    post_utme_required boolean,
    post_utme_format text,
    post_utme_weight_pct integer,
    aggregate_formula text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(institution_id, course_id)
);

-- 9. O-Level subject requirements (normalized, per requirement row)
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

-- 10. UTME subject requirements (normalized)
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

-- 11. Direct Entry requirements (structured)
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

-- 12. Post-UTME rules
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

-- 13. Aggregate formulas (versioned)
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

-- 14. Departmental cut-off marks (per course, per academic session)
create table if not exists departmental_cutoffs (
    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    course_id uuid references courses(id) on delete cascade,
    academic_session text not null,
    merit_cutoff real,
    catchment_cutoff real,
    elds_cutoff real,
    aggregate_formula_id uuid references aggregate_formulas(id) on delete set null,
    source_url text,
    notes text,
    confidence confidence_level not null default 'low',
    created_at timestamptz not null default now(),
    unique(institution_id, course_id, academic_session)
);

-- 15. Catchment areas
create table if not exists catchment (
    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    name text not null,
    eligible_states text[],
    policy text not null default 'geographical', -- 'geographical', 'ELDS', 'none'
    details text,
    created_at timestamptz not null default now(),
    unique(institution_id, name, policy)
);

-- 16. ELDS (Educationally Less Developed States) - shared reference
create table if not exists elds (
    id uuid primary key default uuid_generate_v4(),
    state_name text unique not null,
    is_active boolean default true,
    jamb_session text, -- which JAMB session this list applies to
    notes text,
    created_at timestamptz not null default now()
);

-- Seed ELDS states
insert into elds (state_name, jamb_session) values
    ('Adamawa','2025/2026'), ('Bauchi','2025/2026'), ('Bayelsa','2025/2026'),
    ('Benue','2025/2026'), ('Borno','2025/2026'), ('Cross River','2025/2026'),
    ('Gombe','2025/2026'), ('Jigawa','2025/2026'), ('Kaduna','2025/2026'),
    ('Kano','2025/2026'), ('Katsina','2025/2026'), ('Kebbi','2025/2026'),
    ('Kogi','2025/2026'), ('Kwara','2025/2026'), ('Nasarawa','2025/2026'),
    ('Niger','2025/2026'), ('Plateau','2025/2026'), ('Rivers','2025/2026'),
    ('Sokoto','2025/2026'), ('Taraba','2025/2026'), ('Yobe','2025/2026'),
    ('Zamfara','2025/2026')
on conflict (state_name) do nothing;

-- 17. Fees (detailed, per course/faculty, per session)
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

-- 18. Deadlines
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

-- 19. Admission news / announcements
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

-- 20. Source documents for provenance (linked to Storage)
create table if not exists source_documents (
    id uuid primary key default uuid_generate_v4(),
    institution_id uuid not null references institutions(id) on delete cascade,
    course_id uuid references courses(id) on delete set null,
    url text not null,
    document_type document_type not null default 'webpage',
    title text,
    storage_path text, -- Supabase Storage object path
    storage_bucket text default 'crawl-assets',
    content_hash text,
    crawled_at timestamptz not null default now(),
    date_published timestamptz,
    confidence confidence_level not null default 'low',
    academic_session text,
    raw_content text,
    extracted_data jsonb,
    file_size_bytes integer,
    mime_type text,
    created_at timestamptz not null default now(),
    unique(institution_id, url, crawled_at)
);

-- 21. Crawl logs for audit trail
create table if not exists crawl_logs (
    id uuid primary key default uuid_generate_v4(),
    institution_id uuid references institutions(id) on delete set null,
    institution_name text,
    course_id uuid references courses(id) on delete set null,
    url text not null,
    status crawl_status not null,
    confidence confidence_level not null default 'low',
    source_type document_type not null default 'webpage',
    academic_session text,
    error_message text,
    pages_crawled integer not null default 1,
    metadata jsonb,
    storage_paths text[], -- Supabase Storage paths for screenshots/HTML/PDF
    crawled_at timestamptz not null default now()
);

-- 22. Knowledge versions (complete audit trail)
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

-- ============================================================================
-- STAGING LAYER: Raw crawl data -> Validated data -> Production
-- ============================================================================

-- Raw crawl data: stores everything before validation
create table if not exists raw_crawl_data (
    id uuid primary key default uuid_generate_v4(),
    institution_name text not null,
    institution_id uuid references institutions(id) on delete set null,
    course_name text,
    course_id uuid references courses(id) on delete set null,
    url text not null,
    raw_content text,
    extracted_data jsonb not null,
    content_hash text,
    academic_session text,
    status validation_status not null default 'pending_review',
    reviewed_by text,
    review_notes text,
    reviewed_at timestamptz,
    created_at timestamptz not null default now()
);

-- Validated data: approved raw data ready for promotion to production
create table if not exists validated_data (
    id uuid primary key default uuid_generate_v4(),
    raw_crawl_id uuid not null references raw_crawl_data(id) on delete cascade,
    institution_name text not null,
    institution_id uuid references institutions(id) on delete set null,
    course_name text,
    course_id uuid references courses(id) on delete set null,
    url text not null,
    extracted_data jsonb not null,
    content_hash text,
    academic_session text,
    reviewed_by text not null,
    review_notes text,
    reviewed_at timestamptz not null default now(),
    status validation_status not null default 'approved',
    promoted_at timestamptz,
    promoted_by text,
    created_at timestamptz not null default now()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Institutions
create index if not exists idx_institutions_type on institutions(institution_type);
create index if not exists idx_institutions_state on institutions(state);
create index if not exists idx_institutions_name on institutions(name);
create index if not exists idx_institutions_jamb_code on institutions(jamb_code);

-- Faculties
create index if not exists idx_faculties_inst on faculties(institution_id);

-- Departments
create index if not exists idx_departments_fac on departments(faculty_id);
create index if not exists idx_departments_inst on departments(institution_id);

-- Courses
create index if not exists idx_courses_inst on courses(institution_id);
create index if not exists idx_courses_dept on courses(department_id);
create index if not exists idx_courses_fac on courses(faculty_id);
create index if not exists idx_courses_name on courses(name);

-- Course aliases
create index if not exists idx_course_aliases_canonical on course_aliases(canonical_course_id);
create index if not exists idx_course_aliases_alias on course_aliases(alias);

-- Subjects
create index if not exists idx_subjects_name on subjects(name);
create index if not exists idx_subjects_code on subjects(code);

-- Subject aliases
create index if not exists idx_subject_aliases_canonical on subject_aliases(canonical_subject_id);
create index if not exists idx_subject_aliases_alias on subject_aliases(alias);

-- Admission Requirements
create index if not exists idx_adm_req_inst on admission_requirements(institution_id);
create index if not exists idx_adm_req_course on admission_requirements(course_id);

-- O-Level Requirements
create index if not exists idx_olevel_adm_req on olevel_requirements(admission_requirement_id);
create index if not exists idx_olevel_subject on olevel_requirements(subject_id);

-- UTME Requirements
create index if not exists idx_utme_adm_req on utme_requirements(admission_requirement_id);
create index if not exists idx_utme_subject on utme_requirements(subject_id);

-- Direct Entry
create index if not exists idx_de_adm_req on direct_entry(admission_requirement_id);

-- Post-UTME
create index if not exists idx_postutme_adm_req on post_utme(admission_requirement_id);

-- Aggregate Formulas
create index if not exists idx_agg_form_inst on aggregate_formulas(institution_id);
create index if not exists idx_agg_form_course on aggregate_formulas(course_id);
create index if not exists idx_agg_form_session on aggregate_formulas(effective_from);

-- Departmental Cutoffs
create index if not exists idx_cutoffs_inst on departmental_cutoffs(institution_id);
create index if not exists idx_cutoffs_course on departmental_cutoffs(course_id);
create index if not exists idx_cutoffs_session on departmental_cutoffs(academic_session);

-- Catchment
create index if not exists idx_catchment_inst on catchment(institution_id);

-- ELDS
create index if not exists idx_elds_session on elds(jamb_session);

-- Fees
create index if not exists idx_fees_inst on fees(institution_id);
create index if not exists idx_fees_course on fees(course_id);
create index if not exists idx_fees_session on fees(academic_session);
create index if not exists idx_fees_category on fees(fee_category);

-- Deadlines
create index if not exists idx_deadlines_inst on deadlines(institution_id);
create index if not exists idx_deadlines_course on deadlines(course_id);
create index if not exists idx_deadlines_type on deadlines(deadline_type);
create index if not exists idx_deadlines_session on deadlines(academic_session);
create index if not exists idx_deadlines_date on deadlines(deadline_date);

-- Admission News
create index if not exists idx_news_inst on admission_news(institution_id);
create index if not exists idx_news_category on admission_news(news_category);
create index if not exists idx_news_published on admission_news(published_date desc);
create index if not exists idx_news_hash on admission_news(content_hash);

-- Source Documents
create index if not exists idx_src_doc_inst on source_documents(institution_id);
create index if not exists idx_src_doc_course on source_documents(course_id);
create index if not exists idx_src_doc_hash on source_documents(content_hash);
create index if not exists idx_src_doc_session on source_documents(academic_session);
create index if not exists idx_src_doc_storage on source_documents(storage_path);

-- Crawl Logs
create index if not exists idx_crawl_logs_inst on crawl_logs(institution_id);
create index if not exists idx_crawl_logs_course on crawl_logs(course_id);
create index if not exists idx_crawl_logs_name on crawl_logs(institution_name);
create index if not exists idx_crawl_logs_status on crawl_logs(status);
create index if not exists idx_crawl_logs_crawled on crawl_logs(crawled_at desc);

-- Knowledge Versions
create index if not exists idx_kv_table_record on knowledge_versions(table_name, record_id);
create index if not exists idx_kv_inst on knowledge_versions(institution_id);
create index if not exists idx_kv_created on knowledge_versions(created_at desc);
create index if not exists idx_kv_version on knowledge_versions(version_number);

-- Staging
create index if not exists idx_raw_crawl_status on raw_crawl_data(status);
create index if not exists idx_raw_crawl_hash on raw_crawl_data(content_hash);
create index if not exists idx_raw_crawl_inst on raw_crawl_data(institution_id);
create index if not exists idx_validated_raw on validated_data(raw_crawl_id);
create index if not exists idx_validated_status on validated_data(status);
create index if not exists idx_validated_inst on validated_data(institution_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
alter table institutions enable row level security;
alter table faculties enable row level security;
alter table departments enable row level security;
alter table courses enable row level security;
alter table course_aliases enable row level security;
alter table subjects enable row level security;
alter table subject_aliases enable row level security;
alter table admission_requirements enable row level security;
alter table olevel_requirements enable row level security;
alter table utme_requirements enable row level security;
alter table direct_entry enable row level security;
alter table post_utme enable row level security;
alter table aggregate_formulas enable row level security;
alter table departmental_cutoffs enable row level security;
alter table catchment enable row level security;
alter table elds enable row level security;
alter table fees enable row level security;
alter table deadlines enable row level security;
alter table admission_news enable row level security;
alter table source_documents enable row level security;
alter table crawl_logs enable row level security;
alter table knowledge_versions enable row level security;
alter table raw_crawl_data enable row level security;
alter table validated_data enable row level security;

-- Public read access for production tables
drop policy if exists "Public read institutions" on institutions;
create policy "Public read institutions" on institutions for select using (true);
drop policy if exists "Public read faculties" on faculties;
create policy "Public read faculties" on faculties for select using (true);
drop policy if exists "Public read departments" on departments;
create policy "Public read departments" on departments for select using (true);
drop policy if exists "Public read courses" on courses;
create policy "Public read courses" on courses for select using (true);
drop policy if exists "Public read course_aliases" on course_aliases;
create policy "Public read course_aliases" on course_aliases for select using (true);
drop policy if exists "Public read subjects" on subjects;
create policy "Public read subjects" on subjects for select using (true);
drop policy if exists "Public read subject_aliases" on subject_aliases;
create policy "Public read subject_aliases" on subject_aliases for select using (true);
drop policy if exists "Public read admission_requirements" on admission_requirements;
create policy "Public read admission_requirements" on admission_requirements for select using (true);
drop policy if exists "Public read olevel_requirements" on olevel_requirements;
create policy "Public read olevel_requirements" on olevel_requirements for select using (true);
drop policy if exists "Public read utme_requirements" on utme_requirements;
create policy "Public read utme_requirements" on utme_requirements for select using (true);
drop policy if exists "Public read direct_entry" on direct_entry;
create policy "Public read direct_entry" on direct_entry for select using (true);
drop policy if exists "Public read post_utme" on post_utme;
create policy "Public read post_utme" on post_utme for select using (true);
drop policy if exists "Public read aggregate_formulas" on aggregate_formulas;
create policy "Public read aggregate_formulas" on aggregate_formulas for select using (true);
drop policy if exists "Public read departmental_cutoffs" on departmental_cutoffs;
create policy "Public read departmental_cutoffs" on departmental_cutoffs for select using (true);
drop policy if exists "Public read catchment" on catchment;
create policy "Public read catchment" on catchment for select using (true);
drop policy if exists "Public read elds" on elds;
create policy "Public read elds" on elds for select using (true);
drop policy if exists "Public read fees" on fees;
create policy "Public read fees" on fees for select using (true);
drop policy if exists "Public read deadlines" on deadlines;
create policy "Public read deadlines" on deadlines for select using (true);
drop policy if exists "Public read admission_news" on admission_news;
create policy "Public read admission_news" on admission_news for select using (true);
drop policy if exists "Public read source_documents" on source_documents;
create policy "Public read source_documents" on source_documents for select using (true);
drop policy if exists "Public read crawl_logs" on crawl_logs;
create policy "Public read crawl_logs" on crawl_logs for select using (true);
drop policy if exists "Public read knowledge_versions" on knowledge_versions;
create policy "Public read knowledge_versions" on knowledge_versions for select using (true);

-- Service role has full access (for crawler)
drop policy if exists "Service role full access institutions" on institutions;
create policy "Service role full access institutions" on institutions for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access faculties" on faculties;
create policy "Service role full access faculties" on faculties for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access departments" on departments;
create policy "Service role full access departments" on departments for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access courses" on courses;
create policy "Service role full access courses" on courses for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access course_aliases" on course_aliases;
create policy "Service role full access course_aliases" on course_aliases for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access subjects" on subjects;
create policy "Service role full access subjects" on subjects for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access subject_aliases" on subject_aliases;
create policy "Service role full access subject_aliases" on subject_aliases for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access admission_requirements" on admission_requirements;
create policy "Service role full access admission_requirements" on admission_requirements for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access olevel_requirements" on olevel_requirements;
create policy "Service role full access olevel_requirements" on olevel_requirements for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access utme_requirements" on utme_requirements;
create policy "Service role full access utme_requirements" on utme_requirements for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access direct_entry" on direct_entry;
create policy "Service role full access direct_entry" on direct_entry for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access post_utme" on post_utme;
create policy "Service role full access post_utme" on post_utme for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access aggregate_formulas" on aggregate_formulas;
create policy "Service role full access aggregate_formulas" on aggregate_formulas for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access departmental_cutoffs" on departmental_cutoffs;
create policy "Service role full access departmental_cutoffs" on departmental_cutoffs for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access catchment" on catchment;
create policy "Service role full access catchment" on catchment for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access elds" on elds;
create policy "Service role full access elds" on elds for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access fees" on fees;
create policy "Service role full access fees" on fees for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access deadlines" on deadlines;
create policy "Service role full access deadlines" on deadlines for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access admission_news" on admission_news;
create policy "Service role full access admission_news" on admission_news for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access source_documents" on source_documents;
create policy "Service role full access source_documents" on source_documents for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access crawl_logs" on crawl_logs;
create policy "Service role full access crawl_logs" on crawl_logs for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access knowledge_versions" on knowledge_versions;
create policy "Service role full access knowledge_versions" on knowledge_versions for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access raw_crawl_data" on raw_crawl_data;
create policy "Service role full access raw_crawl_data" on raw_crawl_data for all using (auth.role() = 'service_role');
drop policy if exists "Service role full access validated_data" on validated_data;
create policy "Service role full access validated_data" on validated_data for all using (auth.role() = 'service_role');

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to generate content hash from extracted data
create or replace function generate_content_hash(data jsonb) returns text
language sql immutable as $$
    select encode(digest(data::text, 'sha256'), 'hex');
$$;

-- Function to check if content has changed
create or replace function content_changed(inst_id uuid, url text, new_hash text) returns boolean
language plpgsql as $$
declare
    old_hash text;
begin
    select content_hash into old_hash
    from source_documents
    where institution_id = inst_id and url = $2
    order by crawled_at desc
    limit 1;
    
    if old_hash is null then
        return true; -- New URL, treat as changed
    end if;
    
    return old_hash <> new_hash;
end;
$$;

-- Trigger function to log knowledge versions on insert/update
create or replace function log_knowledge_version()
returns trigger language plpgsql as $$
declare
    v_table_name text := TG_TABLE_NAME;
    v_record_id uuid;
    v_institution_id uuid;
    v_version_number integer;
    v_previous_value jsonb;
    v_new_value jsonb;
    v_changed_fields text[];
    v_source_doc_id uuid;
    v_crawl_log_id uuid;
    v_change_reason text := 'update';
begin
    -- Get the record ID
    if TG_OP = 'INSERT' then
        v_record_id := NEW.id;
        v_change_reason := 'initial_crawl';
    else
        v_record_id := OLD.id;
    end if;
    
    -- Get institution_id from the record (varies by table)
    if v_table_name = 'institutions' then
        v_institution_id := v_record_id;
    elsif v_table_name = 'courses' then
        select institution_id into v_institution_id from courses where id = v_record_id;
    elsif v_table_name = 'departmental_cutoffs' then
        select institution_id into v_institution_id from departmental_cutoffs where id = v_record_id;
    elsif v_table_name = 'admission_requirements' then
        select institution_id into v_institution_id from admission_requirements where id = v_record_id;
    elsif v_table_name = 'fees' then
        select institution_id into v_institution_id from fees where id = v_record_id;
    elsif v_table_name = 'deadlines' then
        select institution_id into v_institution_id from deadlines where id = v_record_id;
    elsif v_table_name = 'admission_news' then
        select institution_id into v_institution_id from admission_news where id = v_record_id;
    elsif v_table_name = 'source_documents' then
        select institution_id into v_institution_id from source_documents where id = v_record_id;
    else
        -- Try common column names
        execute format('select institution_id from %I where id = $1', v_table_name) into v_institution_id using v_record_id;
    end if;
    
    -- Get next version number
    select coalesce(max(version_number), 0) + 1 into v_version_number
    from knowledge_versions
    where table_name = v_table_name and record_id = v_record_id;
    
    -- Build previous and new values
    if TG_OP = 'INSERT' then
        v_previous_value := '{}'::jsonb;
        v_new_value := to_jsonb(NEW);
        v_changed_fields := array(select jsonb_object_keys(to_jsonb(NEW)));
    elsif TG_OP = 'UPDATE' then
        v_previous_value := to_jsonb(OLD);
        v_new_value := to_jsonb(NEW);
        v_changed_fields := array(
            select key from jsonb_each_text(to_jsonb(NEW))
            where value <> (to_jsonb(OLD) ->> key)
        );
    else
        v_previous_value := to_jsonb(OLD);
        v_new_value := '{}'::jsonb;
        v_changed_fields := array(select jsonb_object_keys(to_jsonb(OLD)));
    end if;
    
    -- Insert knowledge version
    insert into knowledge_versions (
        table_name, record_id, institution_id, version_number,
        effective_date, previous_value, new_value, changed_fields,
        source_document_id, crawl_log_id, change_reason
    ) values (
        v_table_name, v_record_id, v_institution_id, v_version_number,
        now(), v_previous_value, v_new_value, v_changed_fields,
        v_source_doc_id, v_crawl_log_id, v_change_reason
    );
    
    return NEW;
end;
$$;

-- Attach versioning triggers to key tables
drop trigger if exists trigger_kv_institutions on institutions;
create trigger trigger_kv_institutions
    after insert or update or delete on institutions
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_courses on courses;
create trigger trigger_kv_courses
    after insert or update or delete on courses
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_cutoffs on departmental_cutoffs;
create trigger trigger_kv_cutoffs
    after insert or update or delete on departmental_cutoffs
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_adm_req on admission_requirements;
create trigger trigger_kv_adm_req
    after insert or update or delete on admission_requirements
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_fees on fees;
create trigger trigger_kv_fees
    after insert or update or delete on fees
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_deadlines on deadlines;
create trigger trigger_kv_deadlines
    after insert or update or delete on deadlines
    for each row execute function log_knowledge_version();

-- Auto-update updated_at on admission_requirements, post_utme, aggregate_formulas
create or replace function update_timestamp()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trigger_update_adm_req_timestamp on admission_requirements;
create trigger trigger_update_adm_req_timestamp
    before update on admission_requirements
    for each row execute function update_timestamp();

drop trigger if exists trigger_update_postutme_timestamp on post_utme;
create trigger trigger_update_postutme_timestamp
    before update on post_utme
    for each row execute function update_timestamp();

drop trigger if exists trigger_update_agg_formula_timestamp on aggregate_formulas;
create trigger trigger_update_agg_formula_timestamp
    before update on aggregate_formulas
    for each row execute function update_timestamp();

-- ============================================================================
-- STORAGE BUCKET SETUP (run separately in Supabase Dashboard or via API)
-- ============================================================================
-- Create these buckets in Supabase Storage:
-- 1. 'crawl-assets' (public: false) - for HTML, PDF, screenshots, markdown
-- 2. 'institution-assets' (public: true) - for logos, public documents
-- 
-- RLS policies for storage:
-- INSERT: auth.role() = 'service_role'
-- SELECT: public read for 'institution-assets', service_role for 'crawl-assets'