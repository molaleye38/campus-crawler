
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