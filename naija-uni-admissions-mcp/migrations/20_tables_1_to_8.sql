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