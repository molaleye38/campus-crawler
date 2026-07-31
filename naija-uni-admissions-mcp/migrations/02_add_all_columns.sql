-- Migration: Add ALL potentially missing columns to ALL 24 tables
-- Safe: uses ADD COLUMN IF NOT EXISTS everywhere
-- Run this FIRST, then re-run supabase_schema.sql

-- ============================================================================
-- INSTITUTIONS
-- ============================================================================
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS short_name text;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS admission_portal text;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS year_established integer;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS jamb_code text;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS contact_email text;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS phone text;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS address text;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS accreditation_body text;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS last_updated timestamptz DEFAULT now();

-- ============================================================================
-- FACULTIES
-- ============================================================================
ALTER TABLE faculties ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE faculties ADD COLUMN IF NOT EXISTS short_name text;

-- ============================================================================
-- DEPARTMENTS
-- ============================================================================
ALTER TABLE departments ADD COLUMN IF NOT EXISTS faculty_id uuid;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS short_name text;
ALTER TABLE departments ADD COLUMN IF NOT EXISTS code text;

-- ============================================================================
-- COURSES
-- ============================================================================
ALTER TABLE courses ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS department_id uuid;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS faculty_id uuid;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS degree text;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS level text;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS duration_years integer;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS affiliated_university text;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS jamb_subject_combination text[];

-- ============================================================================
-- COURSE_ALIASES
-- ============================================================================
ALTER TABLE course_aliases ADD COLUMN IF NOT EXISTS canonical_course_id uuid;
ALTER TABLE course_aliases ADD COLUMN IF NOT EXISTS alias text;
ALTER TABLE course_aliases ADD COLUMN IF NOT EXISTS alias_type text DEFAULT 'abbreviation';

-- ============================================================================
-- SUBJECTS
-- ============================================================================
ALTER TABLE subjects ADD COLUMN IF NOT EXISTS name text;
ALTER TABLE subjects ADD COLUMN IF NOT EXISTS code text;
ALTER TABLE subjects ADD COLUMN IF NOT EXISTS subject_category text;

-- ============================================================================
-- SUBJECT_ALIASES
-- ============================================================================
ALTER TABLE subject_aliases ADD COLUMN IF NOT EXISTS canonical_subject_id uuid;
ALTER TABLE subject_aliases ADD COLUMN IF NOT EXISTS alias text;

-- ============================================================================
-- ADMISSION_REQUIREMENTS
-- ============================================================================
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS olevel_credits_min integer;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS olevel_sittings_max integer DEFAULT 2;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS awaiting_result_accepted boolean DEFAULT true;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS direct_entry_requirements text;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS minimum_jamb integer;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS post_utme_required boolean;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS post_utme_format text;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS post_utme_weight_pct integer;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS aggregate_formula text;
ALTER TABLE admission_requirements ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- ============================================================================
-- OLEVEL_REQUIREMENTS
-- ============================================================================
ALTER TABLE olevel_requirements ADD COLUMN IF NOT EXISTS admission_requirement_id uuid;
ALTER TABLE olevel_requirements ADD COLUMN IF NOT EXISTS subject_id uuid;
ALTER TABLE olevel_requirements ADD COLUMN IF NOT EXISTS is_required boolean DEFAULT true;
ALTER TABLE olevel_requirements ADD COLUMN IF NOT EXISTS min_grade text DEFAULT 'C6';
ALTER TABLE olevel_requirements ADD COLUMN IF NOT EXISTS notes text;

-- ============================================================================
-- UTME_REQUIREMENTS
-- ============================================================================
ALTER TABLE utme_requirements ADD COLUMN IF NOT EXISTS admission_requirement_id uuid;
ALTER TABLE utme_requirements ADD COLUMN IF NOT EXISTS subject_id uuid;
ALTER TABLE utme_requirements ADD COLUMN IF NOT EXISTS is_required boolean DEFAULT true;
ALTER TABLE utme_requirements ADD COLUMN IF NOT EXISTS is_compulsory boolean DEFAULT false;
ALTER TABLE utme_requirements ADD COLUMN IF NOT EXISTS notes text;

-- ============================================================================
-- DIRECT_ENTRY
-- ============================================================================
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS admission_requirement_id uuid;
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS qualification_type text;
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS qualification_subject text;
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS min_grade text;
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS min_cgpa numeric(3,2);
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS accepts_ijmb boolean DEFAULT false;
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS accepts_jupeb boolean DEFAULT false;
ALTER TABLE direct_entry ADD COLUMN IF NOT EXISTS notes text;

-- ============================================================================
-- POST_UTME
-- ============================================================================
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS admission_requirement_id uuid;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS required boolean DEFAULT true;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS format text;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS weight_pct integer;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS min_score integer;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS duration_minutes integer;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS subjects text[];
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS past_questions_url text;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS notes text;
ALTER TABLE post_utme ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- ============================================================================
-- AGGREGATE_FORMULAS
-- ============================================================================
ALTER TABLE aggregate_formulas ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE aggregate_formulas ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE aggregate_formulas ADD COLUMN IF NOT EXISTS formula_text text;
ALTER TABLE aggregate_formulas ADD COLUMN IF NOT EXISTS formula_json jsonb;
ALTER TABLE aggregate_formulas ADD COLUMN IF NOT EXISTS effective_from text;
ALTER TABLE aggregate_formulas ADD COLUMN IF NOT EXISTS effective_to text;
ALTER TABLE aggregate_formulas ADD COLUMN IF NOT EXISTS is_default boolean DEFAULT false;

-- ============================================================================
-- DEPARTMENTAL_CUTOFFS
-- ============================================================================
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS academic_session text;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS merit_cutoff real;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS catchment_cutoff real;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS elds_cutoff real;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS aggregate_formula_id uuid;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS source_url text;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS notes text;
ALTER TABLE departmental_cutoffs ADD COLUMN IF NOT EXISTS confidence text DEFAULT 'low';

-- ============================================================================
-- CATCHMENT
-- ============================================================================
ALTER TABLE catchment ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE catchment ADD COLUMN IF NOT EXISTS name text;
ALTER TABLE catchment ADD COLUMN IF NOT EXISTS eligible_states text[];
ALTER TABLE catchment ADD COLUMN IF NOT EXISTS policy text DEFAULT 'geographical';
ALTER TABLE catchment ADD COLUMN IF NOT EXISTS details text;

-- ============================================================================
-- ELDS
-- ============================================================================
ALTER TABLE elds ADD COLUMN IF NOT EXISTS state_name text;
ALTER TABLE elds ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;
ALTER TABLE elds ADD COLUMN IF NOT EXISTS jamb_session text;
ALTER TABLE elds ADD COLUMN IF NOT EXISTS notes text;

-- ============================================================================
-- FEES
-- ============================================================================
ALTER TABLE fees ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS faculty_id uuid;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS fee_category text;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS amount_ngn integer;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS amount_usd integer;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS currency text DEFAULT 'NGN';
ALTER TABLE fees ADD COLUMN IF NOT EXISTS indigene_amount_ngn integer;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS non_indigene_amount_ngn integer;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS academic_session text;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS is_per_session boolean DEFAULT true;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS payment_schedule text;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS source_url text;
ALTER TABLE fees ADD COLUMN IF NOT EXISTS notes text;

-- ============================================================================
-- DEADLINES
-- ============================================================================
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS deadline_type text;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS deadline_date date;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS academic_session text;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS is_extended boolean DEFAULT false;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS extension_date date;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS source_url text;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS notes text;

-- ============================================================================
-- ADMISSION_NEWS
-- ============================================================================
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS title text;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS content text;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS summary text;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS source_url text;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS published_date timestamptz;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS crawled_at timestamptz DEFAULT now();
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS news_category text;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS is_critical boolean DEFAULT false;
ALTER TABLE admission_news ADD COLUMN IF NOT EXISTS content_hash text;

-- ============================================================================
-- SOURCE_DOCUMENTS
-- ============================================================================
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS url text;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS document_type text DEFAULT 'webpage';
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS title text;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS storage_path text;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS storage_bucket text DEFAULT 'crawl-assets';
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS content_hash text;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS crawled_at timestamptz DEFAULT now();
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS date_published timestamptz;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS confidence text DEFAULT 'low';
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS academic_session text;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS raw_content text;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS extracted_data jsonb;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS file_size_bytes integer;
ALTER TABLE source_documents ADD COLUMN IF NOT EXISTS mime_type text;

-- ============================================================================
-- CRAWL_LOGS
-- ============================================================================
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS institution_name text;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS url text;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS status text;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS confidence text DEFAULT 'low';
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS source_type text DEFAULT 'webpage';
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS academic_session text;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS error_message text;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS pages_crawled integer DEFAULT 1;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS metadata jsonb;
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS storage_paths text[];
ALTER TABLE crawl_logs ADD COLUMN IF NOT EXISTS crawled_at timestamptz DEFAULT now();

-- ============================================================================
-- KNOWLEDGE_VERSIONS
-- ============================================================================
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS table_name text;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS record_id uuid;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS version_number integer;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS effective_date timestamptz;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS previous_value jsonb;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS new_value jsonb;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS changed_fields text[];
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS source_document_id uuid;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS crawl_log_id uuid;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS change_reason text;
ALTER TABLE knowledge_versions ADD COLUMN IF NOT EXISTS created_by text DEFAULT 'crawler';

-- ============================================================================
-- RAW_CRAWL_DATA
-- ============================================================================
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS institution_name text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS course_name text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS url text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS raw_content text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS extracted_data jsonb;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS content_hash text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS academic_session text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS status text DEFAULT 'pending_review';
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS reviewed_by text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS review_notes text;
ALTER TABLE raw_crawl_data ADD COLUMN IF NOT EXISTS reviewed_at timestamptz;

-- ============================================================================
-- VALIDATED_DATA
-- ============================================================================
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS raw_crawl_id uuid;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS institution_name text;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS institution_id uuid;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS course_name text;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS course_id uuid;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS url text;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS extracted_data jsonb;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS content_hash text;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS academic_session text;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS reviewed_by text;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS review_notes text;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS reviewed_at timestamptz DEFAULT now();
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS status text DEFAULT 'approved';
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS promoted_at timestamptz;
ALTER TABLE validated_data ADD COLUMN IF NOT EXISTS promoted_by text;
