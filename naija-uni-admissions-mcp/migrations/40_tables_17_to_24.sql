
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